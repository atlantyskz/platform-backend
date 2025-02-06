from enum import Enum
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin

class Balance(Base, TimestampMixin):
    __tablename__ = 'balances'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True, index=True)
    organization_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('organizations.id', ondelete="CASCADE"), nullable=False)
    atl_tokens: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False, default=0.0)

    organization = so.relationship('Organization', back_populates='balance')
    balance_usages = so.relationship('BalanceUsage', back_populates='balance')

    __table_args__ = (
        sa.UniqueConstraint('organization_id'),
    )