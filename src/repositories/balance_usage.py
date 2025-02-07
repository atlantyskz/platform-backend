from datetime import datetime
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

    async def get_balance_usage(self, user_id: int, organization_id: Optional[int], assistant_id: Optional[int], start_date: Optional[str], end_date: Optional[str], limit: int = 10, offset: int = 0):
        stmt = select(BalanceUsage).where(
            (BalanceUsage.user_id == user_id),
            (BalanceUsage.organization_id == organization_id) 
        )
        
        if assistant_id is not None:
            stmt = stmt.where(BalanceUsage.assistant_id == assistant_id)

        if start_date is not None:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            stmt = stmt.where(BalanceUsage.created_at >= start_date)
        
        if end_date is not None:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            stmt = stmt.where(BalanceUsage.created_at <= end_date)
        stmt = stmt.order_by(BalanceUsage.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)   
        return result.scalars().all()