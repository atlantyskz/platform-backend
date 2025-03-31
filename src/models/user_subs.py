import datetime

import sqlalchemy as sa
import sqlalchemy.orm as orm

from src.models import Base


class UserSubs(Base):
    __tablename__ = 'user_used_promocodes'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))  # Who bought
    promo_id = sa.Column(sa.Integer, sa.ForeignKey('promocodes.id'), nullable=True,
                         default=None)  # Which promo code use
    subscription_id = sa.Column(sa.Integer, sa.ForeignKey('subscriptions.id'))  # which type of subs bought
    bought_date = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    subscription = orm.relationship('Subscription')
