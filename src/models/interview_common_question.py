import sqlalchemy as sa
import sqlalchemy.orm as so

from src.models import Base, TimestampMixin


class InterviewCommonQuestion(Base, TimestampMixin):
    __tablename__ = 'interview_common_questions'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    session_id = sa.Column(
        sa.ForeignKey(
            'assistant_sessions.id',
            ondelete='CASCADE'),
        nullable=False
    )
    question_text = sa.Column(sa.Text, nullable=False)

    session = so.relationship("AssistantSession", back_populates="common_questions")
