
import uuid
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.assigned_assistant import assigned_assistant

class HRTask(Base):
    __tablename__ = 'hr_assistant_tasks'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    session_id: so.Mapped[uuid.UUID] = so.mapped_column(sa.ForeignKey('assistant_sessions.id', ondelete="CASCADE"), nullable=False)
    task_id: so.Mapped[str] = so.mapped_column(sa.String)
    task_status: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    result_data: so.Mapped[dict] = so.mapped_column(sa.JSON, nullable=True)
    task_type: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    created_at: so.Mapped[str] = so.mapped_column(sa.DateTime, default=sa.func.now())
    
    session = so.relationship("AssistantSession", back_populates="tasks")