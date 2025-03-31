import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundException
from src.repositories.balance import BalanceRepository
from src.repositories.balance_usage import BalanceUsageRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.user import UserRepository
from src.repositories.user_cache_balance import UserCacheBalanceRepository
from src.repositories.user_subs import UserSubsRepository


class BalanceController:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.balance_repository = BalanceRepository(session)
        self.balance_usage_repository = BalanceUsageRepository(session)
        self.organization_repository = OrganizationRepository(session)
        self.user_repository = UserRepository(session)
        self.user_sub_repository = UserSubsRepository(session)
        self.user_cache_balance_repository = UserCacheBalanceRepository(session)

    async def get_balance(self, user_id: int) -> dict:
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")
        organization = await self.organization_repository.get_user_organization(user_id)
        if organization is None:
            raise NotFoundException("Organization not found")
        balance = await self.balance_repository.get_balance(organization.id)
        if balance is None:
            balance = await self.balance_repository.create_balance({
                "organization_id": organization.id,
                "atl_tokens": 10
            })
        payload = {
            "balance": round(balance.atl_tokens, 2),
            "free_trial": balance.free_trial
        }
        user_sub = await self.user_sub_repository.user_active_subscription(user_id)
        if user_sub:
            days_left = ""
            if user_sub.subscription and user_sub.subscription.active_month:
                subscription_end = user_sub.bought_date + relativedelta(months=user_sub.subscription.active_month)
                days_left = max((subscription_end - datetime.datetime.now()).days, 0)

            payload['subscription'] = {
                "has_subscription": True,
                "subscription": str(user_sub.subscription.name),
                "days_left": str(days_left)
            }
        else:
            payload['subscription'] = {
                "has_subscription": False,
                "subscription": "",
                "days_left": ""
            }

        return payload

    async def get_balance_usage(self, user_id, assistant_id, start_date, end_date, limit, offset):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")
        organization = await self.organization_repository.get_user_organization(user_id)
        balance_usage = await self.balance_usage_repository.get_balance_usage(user.id, organization.id, assistant_id,
                                                                              start_date, end_date, limit, offset)
        return [
            {
                "id": usage.id,
                "user_id": usage.user_id,
                "organization_id": usage.organization_id,
                "assistant_id": usage.assistant_id,
                "assistant": usage.assistant.name,
                "atl_token_spent": round(usage.atl_token_spent, 2),
                "type": usage.type,
                "created_at": usage.created_at,
            }
            for usage in balance_usage
        ]

    async def get_user_cache_balance(self, user_id):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")

        user_cache = await self.user_cache_balance_repository.get_cache_balance(user_id)
        return user_cache