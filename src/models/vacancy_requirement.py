import uuid
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.assigned_assistant import assigned_assistant

class VacancyRequirement(Base):
    __tablename__ = 'vacancy_requirements'
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    session_id: so.Mapped[uuid.UUID] = so.mapped_column(sa.ForeignKey('assistant_sessions.id', ondelete="CASCADE"), nullable=False)
    requirement_hash : so.Mapped[str] = so.mapped_column(sa.String,index=True)
    requirement_text: so.Mapped[str] = so.mapped_column(sa.String,index=True,nullable=True)

    def __str__(self):
        return f"{self.id}"