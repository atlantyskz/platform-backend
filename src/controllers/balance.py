import datetime
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src import repositories
from src.core.exceptions import NotFoundException


class BalanceController:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.balance_repository = repositories.BalanceRepository(session)
        self.balance_usage_repository = repositories.BalanceUsageRepository(session)
        self.organization_repository = repositories.OrganizationRepository(session)
        self.user_repository = repositories.UserRepository(session)
        self.organization_subscription_repository = repositories.OrganizationSubscriptionRepository(session)
        self.cash_balance_repository = repositories.CashBalanceRepository(session)

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

        organization_active_sub = await (
            self
            .organization_subscription_repository
            .organization_active_subscription(
                organization.id
            )
        )
        if organization_active_sub:
            subscription_end = organization_active_sub.bought_date + timedelta(
                days=organization_active_sub
                .subscription_plan.active_days
            )

            days_left = max((subscription_end - datetime.datetime.now()).days, 0)

            payload['subscription'] = {
                "has_subscription": True,
                "subscription": str(organization_active_sub.subscription_plan.subscription_name),
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

    async def get_cash_balance(self, user_id):
        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")

        cash_balance = await self.cash_balance_repository.cash_balance(user_id)
        return cash_balance
