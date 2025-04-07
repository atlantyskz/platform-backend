import sqlalchemy as sa
import sqlalchemy.orm as orm

from src.models import Base


class CashBalance(Base):
    __tablename__ = "cash_balance"

    id: orm.Mapped[int] = orm.mapped_column(
        sa.Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: orm.Mapped[int] = orm.mapped_column(
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    balance: orm.Mapped[float] = orm.mapped_column(
        sa.Float,
        nullable=False,
        default=0.0
    )

    user = orm.relationship("User", back_populates="cash_balance", uselist=False)
