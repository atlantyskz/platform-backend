import sqlalchemy as sa

from src.models import Base


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    atl_tokens = sa.Column(sa.Float, nullable=False, default=9999.9)
    active_month = sa.Column(sa.Integer, default=1)  # in month
    price = sa.Column(sa.Float, nullable=False)
