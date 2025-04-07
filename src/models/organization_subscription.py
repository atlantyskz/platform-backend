import datetime

import sqlalchemy as sa
import sqlalchemy.orm as orm

from src.models import Base
from src.models import SubscriptionPlan


class OrganizationSubscription(Base):
    __tablename__ = 'organization_subscriptions'

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)

    organization_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    promo_id: orm.Mapped[int | None] = orm.mapped_column(
        sa.ForeignKey('promocodes.id', ondelete='SET NULL'),
        nullable=True,
        default=None
    )

    subscription_id: orm.Mapped[int] = (
        orm.mapped_column(
            sa.ForeignKey('subscription_plans.id', ondelete='CASCADE'),
            nullable=False
        )
    )

    bought_date: orm.Mapped[datetime.datetime] = (
        orm.mapped_column(
            sa.DateTime,
            default=datetime.datetime.utcnow,
            nullable=False
        )
    )

    subscription_plan: orm.Mapped["SubscriptionPlan"] = orm.relationship("SubscriptionPlan")
