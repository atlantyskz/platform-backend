from sqlalchemy.ext.asyncio import AsyncSession

from src import models
from src import repositories
from src.core import exceptions


class BalanceUsageController:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.balance_usage_repository = repositories.BalanceUsageRepository(session)
        self.organization_repository = repositories.OrganizationRepository(session)
        self.user_repository = repositories.UserRepository(session)
        self.balance_repository = repositories.BalanceRepository(session)

    async def create_balance_usage(self, attributes: dict):
        balance_usage = await self.balance_usage_repository.create(attributes)
        return balance_usage

    async def get_balance_usage(self, user_id: int, assistant_id: int, start_date: str, end_date: str):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise exceptions.NotFoundException("User not found")
        organization: models.Organization = await self.organization_repository.get_user_organization(user_id)

        balance_usage = await self.balance_usage_repository.get_balance_usage(
            user.id,
            organization.id,
            assistant_id,
            start_date,
            end_date
        )

        return balance_usage