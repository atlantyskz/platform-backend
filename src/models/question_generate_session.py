import enum

import sqlalchemy as sa
import sqlalchemy.orm as so

from src import models


class GenerateStatus(enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class QuestionGenerateSession(models.Base, models.TimestampMixin):
    __tablename__ = 'resume_generate_session'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    session_id: so.Mapped[str] = so.mapped_column(sa.String)
    status: so.Mapped[GenerateStatus] = so.mapped_column(sa.Enum(GenerateStatus), default=GenerateStatus.PENDING)
    error: so.Mapped[str] = so.mapped_column(sa.String, nullable=True)
