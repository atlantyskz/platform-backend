from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src import models


class OrganizationSubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def organization_active_subscription(self, organization_id: int) -> Optional[models.OrganizationSubscription]:
        stmt = (
            select(models.OrganizationSubscription)
            .options(joinedload(models.OrganizationSubscription.subscription_plan))
            .where(models.OrganizationSubscription.organization_id == organization_id)
        )
        result = await self.session.execute(stmt)
        organization: Optional[models.OrganizationSubscription] = result.scalar_one_or_none()

        if not organization:
            return None

        days = organization.subscription_plan.active_days
        expiration_date = organization.bought_date + timedelta(days=days)

        if expiration_date >= datetime.utcnow():
            return organization
        return None

    async def organization_subscriptions(self, organization_id: int) -> Optional[models.OrganizationSubscription]:
        stmt = (
            select(
                models.OrganizationSubscription
            )
            .join(
                models.SubscriptionPlan,
                models.SubscriptionPlan.id == models.OrganizationSubscription.subscription_id
            )
            .where(
                models.OrganizationSubscription.organization_id == organization_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_organization_subscription(self, data: dict) -> Optional[models.OrganizationSubscription]:
        stmt = insert(models.OrganizationSubscription).values(**data).returning(models.OrganizationSubscription)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def analyze_subscription(self, organization_id: int) -> dict:
        stmt = (
            select(
                models.OrganizationSubscription.id,
                models.User.email,
                models.BillingTransaction.amount,
                models.OrganizationSubscription.bought_date,
                models.SubscriptionPlan.subscription_name,
                models.SubscriptionPlan.price,
            )
            .join(
                models.SubscriptionPlan,
                models.SubscriptionPlan.id == models.OrganizationSubscription.subscription_id
            )
            .join(
                models.BillingTransaction,
                models.BillingTransaction.organization_id == models.OrganizationSubscription.organization_id
            )
            .join(
                models.User, models.User.id == models.BillingTransaction.user_id
            )
            .where(
                models.OrganizationSubscription.organization_id == organization_id
            )
            .distinct()
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        total_income = 0
        items = []

        for row in rows:
            income = row.price * 0.25
            total_income += income
            items.append({
                "id": row.id,
                "email": row.email,
                "bought_date": row.bought_date,
                "income": income,
                "subscription_name": row.subscription_name
            })

        return {
            "count": len(items),
            "total_income": total_income,
            "items": items,
        }
