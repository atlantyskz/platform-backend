import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.assigned_assistant import assigned_assistant  

class Organization(Base,TimestampMixin):

    __tablename__ = 'organizations'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    name: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    email:so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    phone_number: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)
    registered_address: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)
    

    assistants = so.relationship(
        "Assistant",
        secondary=assigned_assistant,
        back_populates="organizations",
        cascade="all"
    )

    members = so.relationship(
        "OrganizationMember",
        back_populates='organization',
        cascade="all, delete-orphan",
        passive_deletes=True
    )
  
    balance = so.relationship('Balance', back_populates='organization', uselist=False)
    balance_usages = so.relationship('BalanceUsage', back_populates='organization')
    billing_transactions = so.relationship('BillingTransaction', back_populates='organization')
    refund_applications = so.relationship('RefundApplication', back_populates='organization')

    def __str__(self):
        return self.name