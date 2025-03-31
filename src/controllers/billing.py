import logging
import uuid
from datetime import datetime

import httpx
from fastapi import File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundException, BadRequestException
from src.repositories.balance import BalanceRepository
from src.repositories.balance_usage import BalanceUsageRepository
from src.repositories.billing_transactions import BillingTransactionRepository
from src.repositories.discount import DiscountRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.promocode import PromoCodeRepository
from src.repositories.refund_application import RefundApplicationRepository
from src.repositories.subscription import SubscriptionRepository
from src.repositories.user import UserRepository
from src.repositories.user_cache_balance import UserCacheBalanceRepository
from src.repositories.user_subs import UserSubsRepository
from src.schemas.requests.billing import TopUpBillingRequest, BuySubscription
from src.services.minio import MinioUploader

logger = logging.getLogger(__name__)


class BillingController:
    ATL_TOKEN_RATE = 230

    def __init__(self, session: AsyncSession):
        self.session = session
        self.billing_transaction_repository = BillingTransactionRepository(session)
        self.balance_usage_repository = BalanceUsageRepository(session)
        self.balance_repository = BalanceRepository(session)
        self.organization_repository = OrganizationRepository(session)
        self.user_repository = UserRepository(session)
        self.discount_repository = DiscountRepository(session)
        self.refund_repository = RefundApplicationRepository(session)
        self.subscription_repository = SubscriptionRepository(session)
        self.user_subs_repository = UserSubsRepository(session)
        self.promocode_repository = PromoCodeRepository(session)
        self.user_cache_balance_repo = UserCacheBalanceRepository(session)
        self.minio_service = MinioUploader(
            host="minio:9000",
            access_key="admin",
            secret_key="admin123",
            bucket_name="analyze-resumes"
        )

    async def refund_application_create(self, user_id: int, transaction_id: int, email: str, reason: str,
                                        file: UploadFile = File(None)):
        async with self.session.begin() as session:
            user = await self.user_repository.get_by_user_id(user_id)
            if user is None:
                raise NotFoundException("User not found")

            organization = await self.organization_repository.get_user_organization(user_id)
            if organization is None:
                raise NotFoundException("Organization not found")
            billing_transaction = await self.billing_transaction_repository.get_transaction(transaction_id, user.id,
                                                                                            organization.id)
            if billing_transaction is None:
                raise NotFoundException("Transaction not found")
            if file is not None:
                if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
                    raise BadRequestException("Invalid file type")
                file_bytes = await file.read()
                permanent_url, file_key = await self.minio_service.upload_single_file(file_bytes,
                                                                                      f"refund_applications/{uuid.uuid4()}_{file.filename}")

            refund_application = await self.refund_repository.create({
                "user_id": user.id,
                "email": email,
                "organization_id": organization.id,
                "transaction_id": transaction_id,
                "reason": reason,
                "status": "pending refund",
                "file_path": file_key if file else None
            })
            await self.billing_transaction_repository.update(
                billing_transaction.id, {"status": "pending refund"}
            )

            return {
                "id": refund_application.id,
                "email": refund_application.email,
                "status": refund_application.status,
            }

    async def top_up_balance(self, user_id: int, request: TopUpBillingRequest):
        """Пополнение баланса через платежную систему"""
        async with self.session.begin() as session:
            user = await self.user_repository.get_by_user_id(user_id)
            if user is None:
                raise NotFoundException("User not found")

            organization = await self.organization_repository.get_user_organization(user_id)
            if organization is None:
                raise NotFoundException("Organization not found")

            kzt_amount = request.atl_amount * self.ATL_TOKEN_RATE
            discount_value, discount_id = await self.discount_checker_by_range(request.atl_amount)
            kzt_amount = kzt_amount * (1 - (discount_value / 100))
            billing_transaction_data = {
                "user_id": user.id,
                "organization_id": organization.id,
                "user_role": user.role.name,
                "discount_id": discount_id if discount_id else None,
                "amount": kzt_amount,
                "atl_tokens": request.atl_amount,
                "access_token": request.access_token,
                "invoice_id": request.invoice_id,
                "type": "balance",
                "status": "pending",
                "payment_type": 'card'
            }
            billing_transaction = await self.billing_transaction_repository.create(billing_transaction_data)
            await self.balance_repository.topup_balance(organization.id, request.atl_amount)

            return {
                "id": billing_transaction.id,
                "amount": billing_transaction.amount,
                "atl_tokens": billing_transaction.atl_tokens,
                "status": billing_transaction.status,
                "payment_type": billing_transaction.payment_type
            }

    async def discount_checker_by_range(self, atl_amount: int):
        if atl_amount <= 100:
            discount = await self.discount_repository.get_discount(5)
            return discount.value, discount.id
        else:
            discount = await self.discount_repository.get_discount(10)
            return discount.value, discount.id

    async def billing_status(self, data: dict):
        async with self.session.begin() as session:
            async with httpx.AsyncClient() as client:
                try:
                    print(data)
                    invoice_id = data.get("invoiceId")
                    billing_transaction = await self.billing_transaction_repository.get_by_invoice_id(invoice_id)

                    bank_transaction_response = await client.get(
                        f"https://epay-api.homebank.kz/check-status/payment/transaction/{invoice_id}",
                        headers={"Authorization": f"Bearer {billing_transaction.access_token}"},
                    )
                    bank_transaction_response.raise_for_status()
                    bank_transaction_response_json = bank_transaction_response.json()
                    print(bank_transaction_response_json)

                    transaction_data = bank_transaction_response_json.get("transaction", {})
                    status_name = transaction_data.get("statusName")
                    transaction_id = transaction_data.get("id")
                    await self.billing_transaction_repository.update(
                        billing_transaction.id, {"bank_transaction_id": transaction_id}
                    )

                    print(status_name)
                    if status_name == "AUTH":
                        print("Charging...")
                        charge_payment = await client.post(
                            f"https://epay-api.homebank.kz/operation/{transaction_id}/charge",
                            headers={"Authorization": f"Bearer {billing_transaction.access_token}"},
                        )
                        charge_payment.raise_for_status()

                        await self.billing_transaction_repository.update(
                            billing_transaction.id, {"status": "charged"}
                        )
                        if billing_transaction.type == "package":
                            await self.user_subs_repository.create_user_subscription({
                                "user_id": billing_transaction.user_id,
                                "promo_id": billing_transaction.promo_id,
                                "subscription_id": billing_transaction.subscription_id,
                                "bought_date": datetime.now(),
                            })
                        elif billing_transaction.type == "balance":
                            await self.balance_repository.topup_balance(
                                billing_transaction.organization_id, billing_transaction.atl_tokens
                            )
                        print("Success Charge")
                        return {"status": "charged"}

                    elif status_name == "CHARGE":
                        print("Already charged, updating balance...")
                        if billing_transaction.type == "package":
                            await self.user_subs_repository.create_user_subscription({
                                "user_id": billing_transaction.user_id,
                                "promo_id": billing_transaction.promo_id,
                                "subscription_id": billing_transaction.subscription_id,
                                "bought_date": datetime.now(),
                            })
                        elif billing_transaction.type == "balance":
                            await self.balance_repository.topup_balance(
                                billing_transaction.organization_id, billing_transaction.atl_tokens
                            )
                        await self.billing_transaction_repository.update(
                            billing_transaction.id, {"status": "charged"}
                        )
                        return {"status": "charged"}

                    else:
                        print("Rejected")
                        await self.billing_transaction_repository.update(
                            billing_transaction.id, {"status": "rejected"}
                        )
                        return {"status": "rejected"}

                except httpx.HTTPStatusError as e:
                    print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
                    return {"error": "HTTP error", "details": e.response.text}

                except Exception as e:
                    print(f"Unexpected error: {str(e)}")
                    return {"error": "Unexpected error", "details": str(e)}

    async def refund_billing_transaction(self, access_token: str, user_id: int, transaction_id: int):
        logger.info(f"Starting refund process for user_id={user_id}, transaction_id={transaction_id}")

        # Retrieve the user
        user = await self.user_repository.get_by_user_id(user_id)
        logger.info(f"User fetched: {user}")
        if user is None:
            logger.error("User not found")
            raise NotFoundException("User not found")

        # Retrieve the organization
        organization = await self.organization_repository.get_user_organization(user_id)
        logger.info(f"Organization fetched: {organization}")
        if organization is None:
            logger.error("Organization not found")
            raise NotFoundException("Organization not found")

        # Retrieve the billing transaction
        billing_transaction = await self.billing_transaction_repository.get_transaction(transaction_id, user.id,
                                                                                        organization.id)
        logger.info(f"Billing transaction fetched: {billing_transaction}")
        if billing_transaction is None:
            logger.error("Transaction not found")
            raise NotFoundException("Transaction not found")

        # Verify the transaction belongs to the organization
        if billing_transaction.organization_id != organization.id:
            logger.error("Transaction does not belong to your organization")
            raise BadRequestException("Transaction does not belong to your organization")

        # Check if transaction status is pending
        if billing_transaction.status == "pending":
            logger.error("Transaction is pending and cannot be refunded")
            raise BadRequestException("Transaction is pending")

        # Check if transaction is already refunded
        if billing_transaction.status == "refunded":
            logger.error("Transaction already fully refunded")
            raise BadRequestException("Transaction already fully refunded")

        # Attempt to process the refund via external API
        async with httpx.AsyncClient() as client:
            try:
                url = f"https://epay-api.homebank.kz/operation/{billing_transaction.bank_transaction_id}/refund"
                logger.info(f"Sending refund request to URL: {url}")

                refund_response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                logger.info(f"Refund response received: {refund_response}")
                refund_response.raise_for_status()
                logger.info("Refund API call successful")

                # Log refund details before updating internal records
                amount = billing_transaction.amount
                atl_tokens_to_refund = billing_transaction.atl_tokens
                logger.info(f"Refund details - Amount: {amount}, ATL Tokens: {atl_tokens_to_refund}")

                # Update the billing transaction status to refunded
                await self.billing_transaction_repository.update(
                    billing_transaction.id, {"status": "refunded"}
                )
                logger.info(f"Billing transaction {billing_transaction.id} updated to 'refunded'")

                # Withdraw the tokens from the organization's balance
                await self.balance_repository.withdraw_balance(
                    billing_transaction.organization_id, atl_tokens_to_refund
                )
                logger.info(
                    f"Withdrew {atl_tokens_to_refund} tokens from organization {billing_transaction.organization_id}")

                logger.info("Refund process completed successfully")
                return {"status": "refunded", "refund_transaction_id": transaction_id}

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=400, detail=f"HTTP Error: {e.response.status_code} - {e.response.text}")

            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Unexpected error: {str(e)}")

    async def get_all_billing_transactions_by_organization_id(self, user_id: int, status: str, limit: int, offset: int):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")

        organization = await self.organization_repository.get_user_organization(user_id)
        if organization is None:
            raise NotFoundException("Organization not found")

        billing_transactions = await self.billing_transaction_repository.get_all_by_organization_id(
            organization.id, status, limit, offset
        )
        return billing_transactions

    async def get_refunds_application(self, user_id: int, status: str, limit: int | None, offset: int | None):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")

        organization = await self.organization_repository.get_user_organization(user_id)
        if organization is None:
            raise NotFoundException("Organization not found")

        refund_application = await self.refund_repository.get_refunds_by_organization_id(organization.id, status, limit,
                                                                                         offset)
        return refund_application

    async def update_refund_application(self, refund_id: int, status: str):
        async with self.session.begin() as session:
            refund_application = await self.refund_repository.get_refund_application(refund_id)

            if refund_application is None:
                raise NotFoundException("Refund application not found")

            # Логируем данные заявки на возврат
            print({
                "refund_id": refund_application.id,
                "refund_status": refund_application.status,
                "transaction_id": refund_application.transaction_id,
                "transaction": refund_application.transaction
            })

            if refund_application.transaction is None:
                raise NotFoundException("Transaction not linked to refund application")

            transaction = await self.billing_transaction_repository.get_transaction(
                refund_application.transaction_id,
                refund_application.user_id,
                refund_application.organization_id
            )

            if transaction is None:
                raise NotFoundException("Transaction not found")

            if transaction.status != 'pending refund':
                raise BadRequestException("Transaction already refunded,pending or rejected")
            print({"retrieved_transaction": transaction})

            if status == 'approved':

                invoice_id = transaction.invoice_id
                amount = transaction.amount

                # Логируем перед запросом в Halyk
                print("Fetching Halyk token with invoice_id:", invoice_id, "amount:", amount)

                try:
                    response = await self.fetch_halyk_token(invoice_id, amount)

                    access_token = response.get("access_token")
                    if not access_token:
                        raise Exception("Failed to get access_token from Halyk")

                    await self.refund_billing_transaction(
                        access_token, refund_application.user_id, refund_application.transaction_id
                    )
                    await self.refund_repository.update_refund(refund_application.id, {"status": "refunded"})
                except httpx.HTTPError as e:
                    raise Exception(f"Halyk API error: {str(e)}")

                return {
                    "id": refund_application.id,
                    "status": "approved"
                }

            elif status == 'rejected':
                await self.refund_repository.update_refund(refund_application.id, {"status": "rejected"})
                return {
                    "id": refund_application.id,
                    "status": "rejected"
                }

            else:
                raise BadRequestException("Invalid status")

    async def fetch_halyk_token(self, unique_invoice_id: str, discounted_price: float):
        url = "https://epay-oauth.homebank.kz/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "scope": "webapi usermanagement email_send verification statement statistics payment",
            "client_id": "ATLANTYS.KZ",
            "client_secret": "p475l5oMEImwOd5X",
            "invoiceID": unique_invoice_id,
            "secret_hash": "HelloWorld123#",
            "amount": str(discounted_price),
            "currency": "KZT",
            "terminal": "5739a558-48e2-49cc-a65b-8f131cd75ed1",
            "postLink": "https://api.atlantys.kz/api/v1/balance/billing-status",
            "failurePostLink": "https://platform.atlantys.kz/payment/failure",
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()

    async def buy_subscription(self, user_id: int, request: BuySubscription):
        async with self.session.begin() as session:
            user = await self.user_repository.get_by_user_id(user_id)
            if user is None:
                raise NotFoundException("User not found")

            organization = await self.organization_repository.get_user_organization(user_id)
            if organization is None:
                raise NotFoundException("Organization not found")

            subscription = await self.subscription_repository.get_subscription(request.subscription_id)
            if not subscription:
                raise BadRequestException("No subscription found")

            active_sub = await self.user_subs_repository.user_active_subscription(user_id)
            if active_sub:
                raise BadRequestException("Active subscription already active")

            promocode = None
            if request.promo_code:
                promocode = await self.promocode_repository.get_promo_code(request.promo_code)
                if not promocode:
                    raise BadRequestException("Promo code not found")

            price_to_pay = subscription.price

            billing_transaction_data = {
                "user_id": user.id,
                "organization_id": organization.id,
                "user_role": user.role.name,
                "discount_id": None,
                "amount": price_to_pay,
                "subscription_id": subscription.id,
                "access_token": request.access_token,
                "invoice_id": request.invoice_id,
                "status": "pending",
                "payment_type": "card",
                "type": "package",
                "promo_id": promocode.id if promocode else None,
            }
            billing_transaction = await self.billing_transaction_repository.create(billing_transaction_data)
            await self.session.flush()

            if promocode:
                promo_owner_id = promocode.user_id

                promo_owner_cache_balance = await self.user_cache_balance_repo.get_cache_balance(promo_owner_id)
                if not promo_owner_cache_balance:
                    promo_owner_cache_balance = await self.user_cache_balance_repo.create_cache_balance(
                        {
                            "user_id": promo_owner_id,
                            "balance": 0,
                        }
                    )

                await self.user_cache_balance_repo.update_cache_balance(
                    user_id=promo_owner_id,
                    data={
                        "balance": promo_owner_cache_balance.balance + (subscription.price - price_to_pay),
                    }
                )
                await self.session.flush()

            return {
                "id": billing_transaction.id,
                "amount": billing_transaction.amount,
                "subscription_id": billing_transaction.subscription_id,
                "status": billing_transaction.status,
                "payment_type": billing_transaction.payment_type
            }
