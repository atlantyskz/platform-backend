from src.models import Base, TimestampMixin

import sqlalchemy as sa
import sqlalchemy.orm as so

class HHAccount(Base):
    __tablename__ = 'hh_accounts'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    access_token = sa.Column(sa.String, nullable=False)
    refresh_token = sa.Column(sa.String, nullable=False)
    expires_at = sa.Column(sa.DateTime, nullable=False)
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now(), nullable=False)
    updated_at = sa.Column(sa.DateTime, onupdate=sa.func.now(), nullable=True)

    user = so.relationship("User", back_populates="hh_account")
