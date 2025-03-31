from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, update, insert, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import UserSubs, Subscription, PromoCode


class UserSubsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def user_active_subscription(self, user_id: int) -> Optional[UserSubs]:
        stmt = (
            select(UserSubs)
            .options(joinedload(UserSubs.subscription))
            .where(UserSubs.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        user_sub: Optional[UserSubs] = result.scalar_one_or_none()

        if not user_sub:
            return None

        months = user_sub.subscription.active_month or 1
        expiration_date = user_sub.bought_date + timedelta(days=30 * months)

        if expiration_date >= datetime.utcnow():
            return user_sub
        return None

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

    async def analyze_subscription(self, user_id: int) -> dict:
        stmt = (
            select(UserSubs, Subscription.price)
            .join(PromoCode, PromoCode.id == UserSubs.promo_id)
            .join(Subscription, Subscription.id == UserSubs.subscription_id)
            .where(PromoCode.user_id == user_id)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        total_price = 0
        user_subs = []

        for user_sub, price in rows:
            user_subs.append(user_sub)
            total_price += price

        return {
            "count": len(user_subs),
            "total_price": total_price,
            "items": user_subs,
        }
