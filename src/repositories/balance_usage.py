from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.balance_usage import BalanceUsage

class BalanceUsageRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, attributes: dict):
        stmt = insert(BalanceUsage).values(**attributes)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalars().first()
    
    async def get_all_by_user_id(self, user_id: int):
        stmt = select(BalanceUsage).where(BalanceUsage.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_all_by_organization_id(self, organization_id: int):
        stmt = select(BalanceUsage).where(BalanceUsage.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    