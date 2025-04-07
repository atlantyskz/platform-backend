from src import repositories
from src.core import exceptions


class SubscriptionPlanController:
    def __init__(self, session):
        self.session = session
        self.subscription_plan_repository = repositories.SubscriptionPlanRepository(self.session)
        self.organization_subscription_repository = repositories.OrganizationSubscriptionRepository(self.session)
        self.balance_repository = repositories.BalanceRepository(self.session)
        self.organization_repository = repositories.OrganizationRepository(self.session)

    async def get_all_subscriptions(self):
        return await self.subscription_plan_repository.get_subscription_plans()

    async def get_organization_active_subscription(self, user_id):
        organization = await self.organization_repository.get_user_organization(user_id)
        if organization is None:
            raise exceptions.NotFoundException("Organization not found")

        organization_subscription = await self.organization_subscription_repository.organization_active_subscription(
            organization.id
        )
        if not organization_subscription:
            raise exceptions.BadRequestException("No active subscription found")
        return organization_subscription
