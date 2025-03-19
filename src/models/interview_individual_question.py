import sqlalchemy as sa
import sqlalchemy.orm as so

from src.models import Base, TimestampMixin


class InterviewIndividualQuestion(Base, TimestampMixin):
    __tablename__ = 'interview_individual_questions'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    session_id = sa.Column(
        sa.ForeignKey(
            'assistant_sessions.id',
            ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    question_text = sa.Column(sa.Text, nullable=False)
    resume_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            'favorite_resumes.id',
            ondelete='CASCADE'
        )
    )