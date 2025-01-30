from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
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
        
    
    
    async def get_all_billing_transactions_by_organization_id(self,user_id:int):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        organization = await self.organization_repository.get_user_organization(user_id)
        if organization is None:
            raise HTTPException(status_code=404, detail="Организация не найдена")
        return await self.billing_transaction_repository.get_all_by_organization_id(organization.id)
    
    async def get_billing_transactions_by_user_id(self,user_id:int):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return await self.billing_transaction_repository.get_all_by_user_id(user.id)
    

    
    async def top_up_balance(self, user_id:int,request: TopUpBillingRequest):
        """Пополнение баланса через платежную систему"""
        async with self.session.begin() as session:
            user = await self.user_repository.get_by_user_id(user_id)
            organization = await self.organization_repository.get_user_organization(user_id)
            kzt_amount = request.atl_amount * self.ATL_TOKEN_RATE

            if request.discount_id:
                discount = await self.discount_repository.get_discount(request.discount_id)
                if discount is None:
                    raise HTTPException(status_code=404, detail="Скидка не найдена")
                kzt_amount = request.atl_amount * self.ATL_TOKEN_RATE * (1 - discount.value)

            billing_transaction = await self.billing_transaction_repository.create({
                {"user_id": user.id,"organization_id":organization.id,
                "user_role":user.role, "amount": kzt_amount, "atl_tokens": request.atl_amount , 
                "status": "pending",'payment_type':request.payment_method}
            })
            
            
            # payment_response = await self.payment_provider.process_payment(transaction)
            
            # if payment_response.success:
            #     balance = await self.db.get_balance(user.organization_id)
            #     balance.atl_tokens += transaction.atl_tokens
            #     transaction.status = "completed"
            #     await self.db.commit()
            # else:
            #     transaction.status = "failed"
            #     await self.db.commit()
            #     raise HTTPException(status_code=400, detail="Ошибка платежа")

            return billing_transaction
