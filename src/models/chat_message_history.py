import uuid
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base, TimestampMixin

class ChatMessageHistory(Base,TimestampMixin):

    __tablename__ = 'chat_history_messages'

    id: so.Mapped[uuid.UUID] = so.mapped_column(
                                                sa.UUID(as_uuid=True),
                                                primary_key=True,
                                                default=uuid.uuid4
    )
    session_id: so.Mapped[uuid.UUID] = so.mapped_column(sa.ForeignKey('assistant_sessions.id', ondelete="CASCADE"), nullable=False)
    vacancy_id: so.Mapped[uuid.UUID] = so.mapped_column(sa.ForeignKey('vacancy.id',ondelete="CASCADE"),nullable=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    role: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)
    message: so.Mapped[dict] = so.mapped_column(sa.JSON,nullable=True)
