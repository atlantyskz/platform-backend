from dataclasses import dataclass, asdict
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src import repositories, models
from src.core import exceptions


@dataclass
class BankCardDTO:
    card_number: str
    id: Optional[int] = None

class BankCardController:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = repositories.BankCardRepository(session)

    async def upsert_bank_card(self, user_id: int, card: BankCardDTO) -> models.BankCard:
        existing_card = await self.repo.get_by_user_id(user_id)
        card_data = asdict(card)

        if existing_card:
            await self.repo.update(user_id, card_data)
            await self.session.commit()
            return existing_card

        card_data['user_id'] = user_id
        new_card = await self.repo.create(card_data)
        await self.session.commit()
        return new_card

    async def get_bank_card(self, user_id: int) -> models.BankCard:
        card = await self.repo.get_by_user_id(user_id)
        if not card:
            raise exceptions.NotFoundException("Bank card not found")
        return card
