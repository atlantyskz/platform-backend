import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.assigned_assistant import assigned_assistant

class FavoriteResume(Base,TimestampMixin):

    __tablename__ = 'favorite_resumes'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    resume_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('hr_assistant_tasks.id', ondelete="CASCADE"), nullable=False)

    user = so.relationship("User", back_populates="favorite_resumes")
    task = so.relationship("HRTask", back_populates="favorites") 


    def __str__(self):
        return f"{self.id}"