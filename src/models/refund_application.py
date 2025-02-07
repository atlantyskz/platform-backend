from src.models import Base,TimestampMixin

import sqlalchemy as sa
import sqlalchemy.orm as so

class RefundApplication(Base,TimestampMixin):
    
    __tablename__ = 'refund_applications'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id'),nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    organization_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('organizations.id'),nullable=False)
    transaction_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('billing_transactions.id'),nullable = False)
    status: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    reason: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    file_path: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)
    user = so.relationship('User',back_populates='refund_applications')
    organization = so.relationship('Organization',back_populates='refund_applications')
    transaction = so.relationship('BillingTransaction',back_populates='refund_applications')
    def __str__(self):
        return f"{self.id}"