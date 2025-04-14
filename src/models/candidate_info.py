import sqlalchemy as sa
import sqlalchemy.orm as orm

from src.models import Base


class CandidateInfo(Base):
    __tablename__ = 'candidate_info'

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    candidate_info: orm.Mapped[str] = orm.mapped_column(sa.JSON, default={}, nullable=True)
    resume_url: orm.Mapped[str] = orm.mapped_column(sa.String, nullable=True)
    hh_resume_url: orm.Mapped[str] = orm.mapped_column(sa.String, nullable=True)

    is_hh: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)