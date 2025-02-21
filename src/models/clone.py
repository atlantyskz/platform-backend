import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin


class Clone(Base,TimestampMixin):

    __tablename__ = 'ai_clones'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id',ondelete='CASCADE'))
    agreement_video_path: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    sample_video_path: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    gender:so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    name:so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    lipsynch_text:so.Mapped[str] = so.mapped_column(sa.String(3000),nullable=False)
    status: so.Mapped[str] = so.mapped_column(sa.String,default='pending')


    def __str__(self):
        return self.id