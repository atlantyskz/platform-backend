from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Subscription


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_subscriptions(self) -> List[Subscription]:
        stmt = select(Subscription)
        subscriptions = await self.session.execute(stmt)
        return subscriptions.scalars().all()

    async def get_subscription(self, subscription_id: int) -> Subscription:
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        subscription = await self.session.execute(stmt)
        subscription = subscription.scalars().first()
        return subscription
