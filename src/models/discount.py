from enum import Enum
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin

class Discount(Base,TimestampMixin):

    __tablename__ =  'discounts'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    name: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    value: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)  

    billing_transactions = so.relationship('BillingTransaction', back_populates='discount')


    def __str__(self):
        return self.id