from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.bank_cards import BankCard
from src.repositories import BaseRepository


class BankCardRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, attributes: dict) -> BankCard:
        bank_card = BankCard(**attributes)
        self.session.add(bank_card)
        await self.session.flush()
        return bank_card

    async def get_by_user_id(self, user_id: int) -> BankCard | None:
        result = await self.session.execute(
            select(BankCard).where(BankCard.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def delete_by_user_id(self, user_id: int) -> BankCard | None:
        result = await self.session.execute(
            select(BankCard).where(BankCard.user_id == user_id)
        )
        bank_card = result.scalar_one_or_none()

        if bank_card:
            await self.session.delete(bank_card)
            await self.session.flush()
        return bank_card

    async def update(self, user_id, attributes: dict) -> BankCard:
        stmt = update(BankCard).where(BankCard.user_id == user_id).values(**attributes)
        await self.session.execute(stmt)
        await self.session.flush()
        return BankCard(**attributes)