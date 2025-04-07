from sqlalchemy import select

from src import models


class SubscriptionPlanRepository:
    def __init__(self, session):
        self.session = session

    async def get_subscription_plans(self):
        stmt = select(models.SubscriptionPlan)
        subscription_plans = await self.session.execute(stmt)
        return subscription_plans.scalars().all()

    async def get_subscription_plan_by_id(self, subscription_plan_id):
        stmt = select(models.SubscriptionPlan).where(models.SubscriptionPlan.id == subscription_plan_id)
        subscription_plan = await self.session.execute(stmt)
        return subscription_plan.scalars().first()