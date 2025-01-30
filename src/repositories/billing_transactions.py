from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.models.billing_transactions import BillingTransaction

class BillingTransactionRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, attributes: dict):
        stmt = insert(BillingTransaction).values(**attributes).returning(BillingTransaction)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all_by_user_id(self, user_id: int):
        stmt = select(BillingTransaction).where(BillingTransaction.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_all_by_organization_id(self, organization_id: int):
        stmt = select(BillingTransaction).join(User, BillingTransaction.user_id == User.id).where(BillingTransaction.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    