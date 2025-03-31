import sqlalchemy as sa
import sqlalchemy.orm as orm

from src.models import Base, TimestampMixin


class PromoCode(Base, TimestampMixin):
    __tablename__ = 'promocodes'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    name = sa.Column(sa.String, nullable=True, default=None)
    email = sa.Column(sa.String)
    phone_number = sa.Column(sa.String)
    is_active = sa.Column(sa.Boolean, default=False)
    promo_code = sa.Column(sa.String)

    user = orm.relationship('User', back_populates='promo_code', uselist=False)
