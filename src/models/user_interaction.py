import datetime

import sqlalchemy as sa

from src.models import Base


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    chat_id = sa.Column(sa.String, nullable=False)
    instance_id = sa.Column(sa.ForeignKey("whatsapp_instances.id", ondelete="CASCADE"), nullable=True)
    messages = sa.Column(sa.JSON, nullable=True, default=[])
    message_type = sa.Column(sa.String, nullable=False)
    is_answered = sa.Column(sa.Boolean, default=False, nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    session_id = sa.Column(sa.ForeignKey("assistant_sessions.id"), nullable=True)
    is_last = sa.Column(sa.Boolean, default=True, nullable=False)