from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_cache_balance import UserCacheBalance


class UserCacheBalanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_cache_balance(self, data: dict) -> UserCacheBalance:
        stmt = insert(UserCacheBalance).values(**data)
        cache_balance = await self.session.execute(stmt)
        return cache_balance.scalar()

    async def get_cache_balance(self, user_id) -> UserCacheBalance:
        stmt = select(UserCacheBalance).where(UserCacheBalance.user_id == user_id)
        cache_balance = await self.session.execute(stmt)
        return cache_balance.scalar()

    async def update_cache_balance(self, user_id: int, data: dict) -> UserCacheBalance:
        stmt = (
            update(UserCacheBalance)
            .where(UserCacheBalance.user_id == user_id)
            .values(**data)
            .returning(
                UserCacheBalance
            )
        )
        cache_balance = await self.session.execute(stmt)
        return cache_balance.scalar()