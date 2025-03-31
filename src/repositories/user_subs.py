from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, insert, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import UserSubs, Subscription, PromoCode


class UserSubsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def user_active_subscription(self, user_id: int) -> Optional[UserSubs]:
        now = datetime.utcnow()

        stmt = (
            select(UserSubs)
            .join(Subscription, UserSubs.subscription_id == Subscription.id)
            .options(joinedload(UserSubs.subscription))
            .where(
                UserSubs.user_id == user_id,
                UserSubs.bought_date + func.make_interval(days=(30 * Subscription.active_month)) >= now
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_user_subscription(self, user_id: int, subscription_id: int, data: dict) -> Optional[UserSubs]:
        stmt = (
            update(UserSubs)
            .where(UserSubs.user_id == user_id, UserSubs.subscription_id == subscription_id)
            .values(**data)
            .returning(UserSubs)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def user_subscriptions(self, user_id: int) -> List[UserSubs]:
        stmt = (
            select(UserSubs)
            .join(Subscription, Subscription.id == UserSubs.subscription_id)
            .where(UserSubs.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def promocode_subscriptions(self, promo_id: int) -> List[UserSubs]:
        stmt = (
            select(UserSubs)
            .join(Subscription, Subscription.id == UserSubs.subscription_id)
            .where(UserSubs.promo_id == promo_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_user_subscription(self, data: dict) -> Optional[UserSubs]:
        stmt = insert(UserSubs).values(**data).returning(UserSubs)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def analyze_subscription(self, user_id: int) -> Optional[UserSubs]:
        stmt = (
            select(
                UserSubs,
                func.sum(Subscription.price).label("total_price"),
                func.count(UserSubs.id).label("count"),
            )
            .select_from(UserSubs)
            .join(PromoCode, PromoCode.id == UserSubs.promo_id)
            .join(Subscription, Subscription.id == UserSubs.subscription_id)
            .where(
                PromoCode.user_id == user_id
            ).group_by(UserSubs.id)
        )

        user_sub = await self.session.execute(stmt)
        return user_sub.scalar()
