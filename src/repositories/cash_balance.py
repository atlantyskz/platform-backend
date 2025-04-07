from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src import models


class CashBalanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_cash_balance(self, data: dict) -> models.CashBalance:
        stmt = insert(models.CashBalance).values(**data).returning(models.CashBalance)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def cash_balance(self, user_id) -> models.CashBalance:
        stmt = select(models.CashBalance).where(models.CashBalance.user_id == user_id)
        cache_balance = await self.session.execute(stmt)
        return cache_balance.scalar()

    async def update_cache_balance(self, user_id: int, data: dict) -> models.CashBalance:
        stmt = (
            update(models.CashBalance)
            .where(models.CashBalance.user_id == user_id)
            .values(**data)
            .returning(
                models.CashBalance
            )
        )
        cash_balance = await self.session.execute(stmt)
        return cash_balance.scalar()
