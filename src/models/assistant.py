import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.assigned_assistant import assigned_assistant

class Assistant(Base,TimestampMixin):

    __tablename__ = 'assistants'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    name: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    description:so.Mapped[str] = so.mapped_column(sa.String,nullable=False)

    type: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)

    organizations = so.relationship(
        "Organization",
        secondary=assigned_assistant,
        back_populates="assistants",
        cascade="all"
    )
    sessions = so.relationship("AssistantSession", back_populates="assistant")