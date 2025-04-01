from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import UserSubs, Subscription, PromoCode, User, BillingTransaction


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
            select(
                UserSubs.id,
                User.email,
                BillingTransaction.amount,
                UserSubs.bought_date,
                Subscription.name,
                Subscription.price
            )
            .select_from(UserSubs)
            .join(PromoCode, PromoCode.id == UserSubs.promo_id)
            .join(Subscription, Subscription.id == UserSubs.subscription_id)
            .join(User, User.id == UserSubs.user_id)
            .join(BillingTransaction, BillingTransaction.user_id == UserSubs.user_id)
            .where(PromoCode.user_id == user_id)
            .distinct()
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        total_price = 0
        items = []

        for row in rows:
            income = row.price * 0.25
            total_price += income
            items.append({
                "id": row.id,
                "email": row.email,
                "bought_date": row.bought_date,
                "income": income,
                "subscription_name": row.name
            })

        return {
            "count": len(items),
            "total_price": total_price,
            "items": items,
        }
