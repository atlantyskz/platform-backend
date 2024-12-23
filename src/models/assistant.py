from enum import Enum
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.assigned_assistant import assigned_assistant

class Assistant(Base,TimestampMixin):

    __tablename__ = 'assistants'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    name: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    description:so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    status:so.Mapped[str] = so.mapped_column(sa.String,nullable=True)
    type: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)

    organizations = so.relationship(
        "Organization",
        secondary=assigned_assistant,
        back_populates="assistants",
        cascade="all"
    )
    sessions = so.relationship("AssistantSession", back_populates="assistant")


class AssistantEnum(Enum):
    HR_ASSISTANT = ('HR Assistant','Handles HR-related tasks','active','my-assistant')

    @property
    def name(self):
        return self.value[0]
    
    @property
    def description(self):
        return self.value[1]

    @property
    def status(self):
        return self.value[2]

    @property
    def type(self):
        return self.value[3]