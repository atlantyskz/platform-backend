import datetime

import sqlalchemy as sa

from src.models import Base


class UserInteraction(Base):
    """
    Represents a single interaction between a user and a WhatsApp instance.

    Fields:
    - id: Unique identifier for the interaction.
    - chat_id: The phone number of the user (receiver).
    - instance_id: The ID of the WhatsApp instance used to send messages (sender).
    - messages: List of exchanged messages (currently unused, reserved for future use).
    - is_answered: Indicates whether this interaction has already been answered in an active session.
    - created_at: Timestamp when the interaction was created.
    - updated_at: Timestamp when the interaction was last updated.
    - session_id: Optional reference to the related assistant session, if any.
    - is_last: True if this is the most recent interaction for the given `chat_id` and `instance_id`.
    - is_ignored: True if this interaction is ignored because another active session exists for the same `chat_id` and `instance_id`.
    - is_hh: True if the WhatsApp instance used is for HeadHunter (HH) integration.
    - is_whatsapp: True if the interaction comes from a standard WhatsApp instance.
    Note:
    - The `messages` field is currently unused but reserved for potential future features.
    """

    __tablename__ = "user_interactions"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    chat_id = sa.Column(sa.String, nullable=False)
    instance_id = sa.Column(sa.ForeignKey("whatsapp_instances.id", ondelete="CASCADE"), nullable=True)
    messages = sa.Column(sa.JSON, nullable=True, default=[])
    is_answered = sa.Column(sa.Boolean, default=False, nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    session_id = sa.Column(sa.ForeignKey("assistant_sessions.id"), nullable=True)
    is_last = sa.Column(sa.Boolean, default=True, nullable=False)
    is_ignored = sa.Column(sa.Boolean, default=False, nullable=True)
    is_hh = sa.Column(sa.Boolean, default=False)
    is_whatsapp = sa.Column(sa.Boolean, default=False)
