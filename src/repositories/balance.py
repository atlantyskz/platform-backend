from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.balance import Balance


class BalanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_balance(self, organization_id: int) -> Balance:
        stmt = select(Balance).where(Balance.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_balance(self, attributes: dict) -> Balance:
        stmt = insert(Balance).values(**attributes).returning(Balance)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_balance(self, organization_id: int, data: dict) -> Balance:
        stmt = (
            update(Balance).where(
                Balance.organization_id == organization_id
            )
            .values(
                **data
            )
            .returning(
                Balance
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def topup_balance(self, organization_id: int, amount: float):
        stmt = (
            update(Balance)
            .where(Balance.organization_id == organization_id)
            .values(atl_tokens=Balance.atl_tokens + amount)
            .returning(Balance)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def withdraw_balance(self, organization_id: int, amount: float):
        stmt = (
            update(Balance)
            .where(Balance.organization_id == organization_id)
            .values(atl_tokens=Balance.atl_tokens - amount)
            .returning(Balance)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def transfer_balance(self, sender_id: int, receiver_id: int, amount: float):
        stmt = (
            update(Balance)
            .where(Balance.organization_id == sender_id)
            .values(atl_tokens=Balance.atl_tokens - amount)
            .returning(Balance)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        stmt = (
            update(Balance)
            .where(Balance.organization_id == receiver_id)
            .values(atl_tokens=Balance.atl_tokens + amount)
            .returning(Balance)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
