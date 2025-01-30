from enum import Enum
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin


class BalanceUsage(Base, TimestampMixin):
    __tablename__ = 'balance_usage'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True, index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    organization_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('organizations.id', ondelete="CASCADE"), nullable=False)
    balance_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('balances.id', ondelete="CASCADE"), nullable=False)
    input_text_count: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, default=0)
    gpt_token_spent: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, default=0)
    input_token_count: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, default=0)
    file_count: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, default=0)
    file_size: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True, default=None)  
    atl_token_spent: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)

    user = so.relationship('User', back_populates='balance_usages')
    organization = so.relationship('Organization', back_populates='balance_usages')
    balance = so.relationship('Balance', back_populates='balance_usages')
    