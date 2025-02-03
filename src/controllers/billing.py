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
        
    
    async def billing_status(self,data:dict):
        async with self.session.begin() as session:
            httpx_client = httpx.AsyncClient()
            async with httpx_client as client:
                invoice_id = data.get('invoice_id') 
                billing_transaction = await self.billing_transaction_repository.get_by_invoice_id(invoice_id)
                bank_transaction_response = await client.get(f'https://testepay.homebank.kz/api/check-status/payment/transaction/{invoice_id}',headers={'Authorization':f'Bearer {billing_transaction.access_token}'})
                bank_transaction_response.raise_for_status()
                statusName = bank_transaction_response.json().get('transaction').get('statusName')
                transaction_id = bank_transaction_response.json().get('transaction').get('id')
                if statusName =='AUTH':
                    charge_payment = await client.post(f"https://testepay.homebank.kz/api/operation/{transaction_id}/charge",headers={'Authorization':f'Bearer {billing_transaction.access_token}'})
                    charge_payment.raise_for_status()
                    await self.billing_transaction_repository.update(billing_transaction.id,{"status":"charged"})
                    await self.balance_repository.topup_balance(billing_transaction.organization_id,billing_transaction.atl_tokens)
                    return {"status":"charged"}
                else:
                    await self.billing_transaction_repository.update(billing_transaction.id,{"status":"rejected"})
                return billing_transaction

    async def get_all_billing_transactions_by_organization_id(self,user_id:int):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")
        organization = await self.organization_repository.get_user_organization(user_id)
        if organization is None:
            raise NotFoundException("Organization not found")
        return await self.billing_transaction_repository.get_all_by_organization_id(organization.id)
    
    async def get_billing_transactions_by_user_id(self,user_id:int):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")
        return await self.billing_transaction_repository.get_all_by_user_id(user.id)
    

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