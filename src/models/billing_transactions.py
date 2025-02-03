from enum import Enum
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin


class BillingTransaction(Base, TimestampMixin):
    __tablename__ = 'billing_transactions'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True, index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    organization_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('organizations.id', ondelete="CASCADE"), nullable=False)
    amount: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False, default=0)
    user_role: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    atl_tokens: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    discount_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('discounts.id', ondelete="SET NULL"), nullable=True)  # Теперь можно не применять скидку
    status: so.Mapped[str] = so.mapped_column(sa.String, default='pending')
    access_token: so.Mapped[str] = so.mapped_column(sa.String, nullable=True)
    invoice_id: so.Mapped[str] = so.mapped_column(sa.String, nullable=True) 
    payment_type: so.Mapped[str] = so.mapped_column(sa.String, nullable=True)

    user = so.relationship('User', back_populates='billing_transactions')
    organization = so.relationship('Organization', back_populates='billing_transactions')
    discount = so.relationship('Discount', back_populates='billing_transactions')
    