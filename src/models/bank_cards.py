import sqlalchemy as sa
import sqlalchemy.orm as orm

from src.models import Base


class BankCard(Base):
    __tablename__ = "bank_cards"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    card_number = sa.Column(sa.String)

    user = orm.relationship("User", back_populates="bank_card", uselist=False)
