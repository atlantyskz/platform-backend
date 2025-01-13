import uuid
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base, TimestampMixin
from src.models.role import role_permissions

class AssistantSession(Base, TimestampMixin):
    __tablename__ = 'assistant_sessions'
    
    id: so.Mapped[uuid.UUID] = so.mapped_column(
                                                sa.UUID(as_uuid=True),
                                                primary_key=True,
                                                default=uuid.uuid4
    )
    
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    title: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)
    is_archived: so.Mapped[bool] = so.mapped_column(sa.Boolean,default=False,nullable=True)
    organization_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('organizations.id', ondelete="CASCADE"), nullable=False)
    assistant_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('assistants.id', ondelete="CASCADE"), nullable=False)  
    
    tasks = so.relationship("HRTask", back_populates="session", cascade="all, delete-orphan") 
    assistant = so.relationship("Assistant", back_populates="sessions")
    vacancies = so.relationship("Vacancy",back_populates="session")