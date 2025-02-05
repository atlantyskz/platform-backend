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
    
    async def get_balance_usage(self, user_id: int, assistant_id: int, start_date: str, end_date: str):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")
        organization = await self.organization_repository.get_user_organization(user_id)
        balance_usage = await self.balance_usage_repository.get_balance_usage(user.id, organization.id, assistant_id, start_date, end_date)
        return balance_usage