import datetime

import sqlalchemy as sa

from src.models import Base


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    chat_id = sa.Column(sa.String, nullable=False)
    session_id = sa.Column(sa.Integer, nullable=True)
    message_type = sa.Column(sa.String, nullable=False)
    is_answered = sa.Column(sa.Boolean, default=False, nullable=False)
    chosen_button = sa.Column(sa.String, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
