import uuid
from fastapi import File, HTTPException, UploadFile
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.minio import MinioUploader
from src.core.exceptions import NotFoundException, BadRequestException
from src.repositories.discount import DiscountRepository
from src.repositories.billing_transactions import BillingTransactionRepository
from src.repositories.balance_usage import BalanceUsageRepository
from src.repositories.balance import BalanceRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.user import UserRepository
from src.schemas.requests.billing import TopUpBillingRequest
from src.repositories.refund_application import RefundApplicationRepository
import httpx




class BillingController:

    ATL_TOKEN_RATE = 230
    def __init__(self,session:AsyncSession):
        self.session = session
        self.billing_transaction_repository = BillingTransactionRepository(session)
        self.balance_usage_repository = BalanceUsageRepository(session)
        self.balance_repository = BalanceRepository(session)
        self.organization_repository = OrganizationRepository(session)
        self.user_repository = UserRepository(session)
        self.discount_repository = DiscountRepository(session)
        self.refund_repository = RefundApplicationRepository(session)
        self.minio_service = MinioUploader(
        host="minio:9000",  
        access_key="admin",
        secret_key="admin123",
        bucket_name="analyze-resumes"
    )
                
    
    async def refund_application_create(self, user_id: int,transaction_id:int, email: str, reason: str, file:UploadFile = File(None)): 
        async with self.session.begin() as session:
            user = await self.user_repository.get_by_user_id(user_id)
            if user is None:
                raise NotFoundException("User not found")
            
            organization = await self.organization_repository.get_user_organization(user_id)
            if organization is None:
                raise NotFoundException("Organization not found")
            billing_transaction = await self.billing_transaction_repository.get_transaction(transaction_id, user.id, organization.id)
            if billing_transaction is None:
                raise NotFoundException("Transaction not found")
            if file is not None:
                if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
                    raise BadRequestException("Invalid file type")
                file_bytes = await file.read()
                permanent_url, file_key = await self.minio_service.upload_single_file(file_bytes, f"refund_applications/{uuid.uuid4()}_{file.filename}")   

            
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
                "status": "pending",
                "payment_type": 'card'
            }
            billing_transaction = await self.billing_transaction_repository.create(billing_transaction_data)
            # await self.balance_repository.topup_balance(organization.id, request.atl_amount)
            
            return {
                "id": billing_transaction.id,
                "amount": billing_transaction.amount,
                "atl_tokens": billing_transaction.atl_tokens,
                "status": billing_transaction.status,
                "payment_type": billing_transaction.payment_type
            }
    
    async def discount_checker_by_range(self,atl_amount: int):
        if atl_amount <= 100 :
            discount = await self.discount_repository.get_discount(5)
            return discount.value,discount.id
        elif atl_amount <= 300:
            discount = await self.discount_repository.get_discount(10)
            return discount.value,discount.id
        elif atl_amount <= 500:
            discount = await self.discount_repository.get_discount(15)
            return discount.value,discount.id
        elif atl_amount <= 1000:
            discount = await self.discount_repository.get_discount(20)
            return discount.value,discount.id
        elif atl_amount <= 5000:
            discount = await self.discount_repository.get_discount(25)
            return discount.value,discount.id
        elif atl_amount <= 10000 or atl_amount > 10000:
            discount = await self.discount_repository.get_discount(30)
            return discount.value,discount.id
        else:
            return 0,None

    async def billing_status(self, data: dict):
        async with self.session.begin() as session:
            async with httpx.AsyncClient() as client:
                try:
                    print(data)
                    invoice_id = data.get("invoiceId")
                    billing_transaction = await self.billing_transaction_repository.get_by_invoice_id(invoice_id)

                    bank_transaction_response = await client.get(
                        f"https://testepay.homebank.kz/api/check-status/payment/transaction/{invoice_id}",
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
                            f"https://testepay.homebank.kz/api/operation/{transaction_id}/charge",
                            headers={"Authorization": f"Bearer {billing_transaction.access_token}"},
                        )
                        charge_payment.raise_for_status()

                        await self.billing_transaction_repository.update(
                            billing_transaction.id, {"status": "charged"}
                        )
                        await self.balance_repository.topup_balance(
                            billing_transaction.organization_id, billing_transaction.atl_tokens
                        )
                        print("Success Charge")
                        return {"status": "charged"}

                    elif status_name == "CHARGE":
                        print("Already charged, updating balance...")
                        await self.billing_transaction_repository.update(
                            billing_transaction.id, {"status": "charged"}
                        )
                        await self.balance_repository.topup_balance(
                            billing_transaction.organization_id, billing_transaction.atl_tokens
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

            user = await self.user_repository.get_by_user_id(user_id)
            if user is None:
                raise NotFoundException("User not found")
            
            organization = await self.organization_repository.get_user_organization(user_id)
            if organization is None:
                raise NotFoundException("Organization not found")
            
            billing_transaction = await self.billing_transaction_repository.get_transaction(transaction_id, user.id, organization.id)
            if billing_transaction is None:
                raise NotFoundException("Transaction not found")
            
            if billing_transaction.organization_id != organization.id:
                raise BadRequestException("Transaction does not belong to your organization")
        
            if billing_transaction.status == "pending":
                raise BadRequestException("Transaction is pending")
            

            if billing_transaction.status == "refunded":
                raise BadRequestException("Transaction already fully refunded")

            async with httpx.AsyncClient() as client:
                try:
                    url = f"https://testepay.homebank.kz/api/operation/{billing_transaction.bank_transaction_id}/refund"

                    refund_response = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    print(refund_response)
                    refund_response.raise_for_status()

                    amount = billing_transaction.amount
                    atl_tokens_to_refund = billing_transaction.atl_tokens


                    await self.billing_transaction_repository.update(
                        billing_transaction.id, {"status": "refunded"}
                    )

                    await self.balance_repository.withdraw_balance(
                        billing_transaction.organization_id, atl_tokens_to_refund
                    )

                    return {"status": "refunded", "refund_transaction_id": transaction_id}

                except httpx.HTTPStatusError as e:
                    print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
                    raise HTTPException(status_code=400, detail=f"HTTP Error: {e.response.status_code} - {e.response.text}")

                except Exception as e:
                    print(f"Unexpected error: {str(e)}")
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
    
    async def get_refunds_application(self, user_id: int,status:str,limit: int|None, offset: int|None):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")
        
        organization = await self.organization_repository.get_user_organization(user_id)
        if organization is None:
            raise NotFoundException("Organization not found")
        
        refund_application = await self.refund_repository.get_refunds_by_organization_id(organization.id,status, limit, offset)
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

          
    async def fetch_halyk_token(self,unique_invoice_id: str, discounted_price: float):
        url = "https://testoauth.homebank.kz/epay2/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "scope": "webapi usermanagement email_send verification statement statistics payment",
            "client_id": "test",
            "client_secret": "yF587AV9Ms94qN2QShFzVR3vFnWkhjbAK3sG",
            "invoiceID": unique_invoice_id,
            "secret_hash": "HelloWorld123#",
            "amount": str(discounted_price),
            "currency": "KZT",
            "terminal": "67e34d63-102f-4bd1-898e-370781d0074d",
            "postLink": "https://api.atlantys.kz/api/v1/balance/billing-status",
            "failurePostLink": "https://platform.atlantys.kz/payment/failure",
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            response.raise_for_status() 
            return response.json()