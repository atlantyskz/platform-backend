import sqlalchemy as sa
import sqlalchemy.orm as orm

from src.models import Base


class SubscriptionPlan(Base):
    __tablename__ = 'subscription_plans'

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    subscription_name: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False)

    limit_queries: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=1000, nullable=False)
    limit_web_ai: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=50, nullable=False)
    limit_members: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=3, nullable=False)

    active_days: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=1, nullable=False)  # in days

    price: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)
