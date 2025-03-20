import enum
import uuid

import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects import postgresql

from src.models import Base, TimestampMixin


class CallStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IS_CALLED = "is_called"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BUSY = "busy"


class FavoriteResume(Base, TimestampMixin):
    __tablename__ = 'favorite_resumes'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True, index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    session_id: so.Mapped[uuid.UUID] = so.mapped_column(sa.ForeignKey('assistant_sessions.id', ondelete="CASCADE"),
                                                        nullable=True)
    resume_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('hr_assistant_tasks.id', ondelete="CASCADE"),
                                                 nullable=False)
    question_for_candidate: so.Mapped[dict] = so.mapped_column(sa.JSON(), nullable=True)
    stage: so.Mapped[str] = so.mapped_column(sa.String, nullable=True, default='phone interview')
    phone_number: so.Mapped[str] = so.mapped_column(sa.String, nullable=True, )

    recording_file: so.Mapped[str] = so.mapped_column(sa.String, nullable=True)
    is_responded: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, nullable=True)
    call_sid: so.Mapped[str] = so.mapped_column(sa.String, nullable=True, )
    call_status: so.Mapped[str] = so.mapped_column(postgresql.ENUM(CallStatus, name='callstatus', create_type=False), nullable=True)

    user = so.relationship("User", back_populates="favorite_resumes")
    task = so.relationship("HRTask", back_populates="favorites")

    def __str__(self):
        return f"{self.id}"
