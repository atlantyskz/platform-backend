import uuid
from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.assigned_assistant import assigned_assistant

class HRTask(Base):
    __tablename__ = 'hr_assistant_tasks'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    session_id: so.Mapped[uuid.UUID] = so.mapped_column(sa.ForeignKey('assistant_sessions.id', ondelete="CASCADE"), nullable=False)
    task_id: so.Mapped[str] = so.mapped_column(sa.String)
    resume_id: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)
    vacancy_id: so.Mapped[int] = so.mapped_column(sa.Integer,nullable=True)
    task_status: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    text_hash: so.Mapped[str] = so.mapped_column(sa.String, nullable=True,index=True)
    result_data: so.Mapped[dict] = so.mapped_column(sa.JSON, nullable=True)
    tokens_spent: so.Mapped[int] = so.mapped_column(sa.Integer,nullable=True)
    task_type: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    file_key: so.Mapped[str] = so.mapped_column(sa.String, nullable=True) 
    created_at: so.Mapped[str] = so.mapped_column(sa.DateTime, default=datetime.utcnow)
    hh_file_url: so.Mapped[str] = so.mapped_column(sa.String, nullable=True)
    session = so.relationship("AssistantSession", back_populates="tasks")
    favorites = so.relationship("FavoriteResume", back_populates="task", cascade="all, delete-orphan")

    def __str__(self):
        return f"{self.id}"