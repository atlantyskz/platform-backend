import uuid
from fastapi import HTTPException
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundException, BadRequestException
from src.repositories.discount import DiscountRepository
from src.repositories.billing_transactions import BillingTransactionRepository
from src.repositories.balance_usage import BalanceUsageRepository
from src.repositories.balance import BalanceRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.user import UserRepository
from src.schemas.requests.billing import TopUpBillingRequest
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


    async def refund_billing_transaction(self, access_token: str, amount: float, user_id: int, transaction_id: int):
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
        
        existing_refunds = await self.billing_transaction_repository.get_refunds_by_transaction(transaction_id)
        refunded_amount = sum(refund.amount for refund in existing_refunds)
        
        if refunded_amount + amount > billing_transaction.amount:
            raise BadRequestException("Refund amount exceeds original transaction")

        async with self.session.begin() as session:
            async with httpx.AsyncClient() as client:
                try:
                    url = f"https://testepay.homebank.kz/api/operation/{billing_transaction.bank_transaction_id}/refund"
                    external_id = str(uuid.uuid4())

                    if amount is not None:
                        url += f"?amount={amount}"
                    url += f"{'&' if amount is not None else '?'}externalID={external_id}" 

                    refund_response = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    refund_response.raise_for_status()

                    atl_tokens_to_refund = round((amount / billing_transaction.amount,2) * billing_transaction.atl_tokens)

                    refund_transaction = await self.billing_transaction_repository.create({
                        "user_id": user.id,
                        "organization_id": organization.id,
                        "amount": amount,
                        "atl_tokens": atl_tokens_to_refund,
                        "type": "refund",
                        "status": "refunded",
                        "payment_type": billing_transaction.payment_type,
                        "bank_transaction_id": billing_transaction.bank_transaction_id,
                        "access_token": access_token,
                        "external_id": external_id,
                        "parent_transaction_id": billing_transaction.id
                    })

                    if refunded_amount + amount == billing_transaction.amount:
                        await self.billing_transaction_repository.update(
                            billing_transaction.id, {"status": "fully_refunded"}
                        )

                    await self.balance_repository.withdraw_balance(
                        billing_transaction.organization_id, atl_tokens_to_refund
                    )

                    return {"status": "refunded", "refund_transaction_id": refund_transaction.id}

                except httpx.HTTPStatusError as e:
                    print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
                    return {"error": "HTTP error", "details": e.response.text}

                except Exception as e:
                    print(f"Unexpected error: {str(e)}")
                    return {"error": "Unexpected error", "details": str(e)}
