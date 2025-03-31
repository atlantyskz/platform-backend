from datetime import datetime, timedelta

from src.core.exceptions import BadRequestException
from src.core.tasks import handle_user_sub
from src.repositories.balance import BalanceRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.subscription import SubscriptionRepository
from src.repositories.user_subs import UserSubsRepository


class SubsController:
    def __init__(self, session):
        self.session = session
        self.subs_repo = SubscriptionRepository(self.session)
        self.user_subs_repo = UserSubsRepository(self.session)
        self.user_subs = UserSubsRepository(self.session)
        self.balance = BalanceRepository(self.session)
        self.organization_repo = OrganizationRepository(self.session)

    async def get_all_subscriptions(self):
        return await self.subs_repo.get_subscriptions()

    async def get_subscription(self, subscription_id):
        return await self.subs_repo.get_subscription(subscription_id)

    async def buy_subscription(self, subscription_id, user_id, promo_id):
        subscription = await self.subs_repo.get_subscription(subscription_id)
        if not subscription:
            raise BadRequestException("No subscription found")

        active_sub = await self.user_subs.user_active_subscription(user_id)
        if active_sub:
            raise BadRequestException("Active subscription already active")

        organization = await self.organization_repo.get_user_organization(user_id)

        async with self.session.begin():
            await self.balance.update_balance(organization.id, {"subscription": True})

            result = await self.user_subs.create_user_subscription({
                "user_id": user_id,
                "promo_id": promo_id,
                "subscription_id": subscription_id,
                "bought_date": datetime.utcnow(),
            })

        days = subscription.active_month * 30
        handle_user_sub.apply_async(
            kwargs={"user_id": user_id, "organization_id": organization.id},
            eta=datetime.utcnow() + timedelta(days=days)
        )
        return result

    async def analyze_subs_user(self, user_id):
        analyze = await self.user_subs_repo.analyze_subscription(user_id)
        if not analyze:
            return {}
        return analyze

    async def get_user_active_subscriptions(self, user_id):
        return await self.user_subs_repo.user_active_subscription(user_id)
