from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.balance_usage import BalanceUsageRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.user import UserRepository
from src.repositories.balance import BalanceRepository
from src.core.exceptions import NotFoundException

class BalanceUsageController:

    def __init__ (self, session: AsyncSession):
        self.session = session
        self.balance_usage_repository = BalanceUsageRepository(session)
        self.organization_repository = OrganizationRepository(session)
        self.user_repository = UserRepository(session)
        self.balance_repository = BalanceRepository(session)

    async def create_balance_usage(self, attributes: dict):
        balance_usage = await self.balance_usage_repository.create(attributes)
        return balance_usage    