from datetime import datetime
from typing import Optional
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.balance_usage import BalanceUsage
from sqlalchemy.orm import joinedload

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
        ).options(joinedload(BalanceUsage.assistant))

        if assistant_id is not None:
            stmt = stmt.where(BalanceUsage.assistant_id == assistant_id)

        # Если заданы и start_date, и end_date – фильтруем по диапазону
        if start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            stmt = stmt.where(
                BalanceUsage.created_at >= start_dt,
                BalanceUsage.created_at <= end_dt
            )
        elif start_date and not end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            stmt = stmt.where(
                BalanceUsage.created_at >= start_dt,
                BalanceUsage.created_at <= end_dt
            )
        elif end_date and not start_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            start_dt = end_dt  # начало дня (по умолчанию 00:00:00)
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            stmt = stmt.where(
                BalanceUsage.created_at >= start_dt,
                BalanceUsage.created_at <= end_dt
            )

        stmt = stmt.order_by(BalanceUsage.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()