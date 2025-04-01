from src.core.exceptions import NotFoundException
from src.repositories.bank_cards import BankCardRepository
from src.schemas.requests.bank_card import BankCardCreate


class BankCardController:
    def __init__(self, session):
        self.session = session
        self.repo = BankCardRepository(self.session)

    async def upsert_bank_card(self, user_id, data: BankCardCreate):
        existing = await self.repo.get_by_user_id(user_id)
        data = data.dict()
        if existing:
            await self.repo.update(user_id, data)
            return existing
        else:
            data['user_id'] = user_id
            created = await self.repo.create(data)
            return created

    async def get_bank_card(self, user_id):
        existing = await self.repo.get_by_user_id(user_id)
        if not existing:
            raise NotFoundException("Bank card not found")
        return existing
