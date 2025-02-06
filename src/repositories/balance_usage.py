from typing import Optional
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.balance_usage import BalanceUsage

class BalanceUsageRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, attributes: dict):
        stmt = insert(BalanceUsage).values(**attributes)
        result = await self.session.execute(stmt)
        # Remove the explicit flush here
        return result.scalars().first()    
    async def get_all_by_user_id(self, user_id: int):
        stmt = select(BalanceUsage).where(BalanceUsage.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_all_by_organization_id(self, organization_id: int):
        stmt = select(BalanceUsage).where(BalanceUsage.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_balance_usage(self, user_id: Optional[int], organization_id: Optional[int], assistant_id: Optional[int], start_date: Optional[str], end_date: Optional[str]):
        filters = []
        
        if user_id is not None:
            filters.append(BalanceUsage.user_id == user_id)
        if organization_id is not None:
            filters.append(BalanceUsage.organization_id == organization_id)
        if assistant_id is not None:
            filters.append(BalanceUsage.assistant_id == assistant_id)
        if start_date is not None:
            filters.append(BalanceUsage.created_at >= start_date)
        if end_date is not None:
            filters.append(BalanceUsage.created_at <= end_date)
        
        stmt = select(BalanceUsage).filter(*filters).order_by(BalanceUsage.created_at)
        result = await self.session.execute(stmt)
        return result.scalars().all()