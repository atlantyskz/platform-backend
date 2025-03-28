import sqlalchemy as sa
import sqlalchemy.orm as orm

from src.models import Base


class UserCacheBalance(Base):
    __tablename__ = 'user_cache_balance'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    balance = sa.Column(sa.Float, default=0)

    user = orm.relationship('User', back_populates='user_cache_balance', uselist=False)