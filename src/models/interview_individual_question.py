import sqlalchemy as sa

from src.models import Base, TimestampMixin


class InterviewIndividualQuestion(Base, TimestampMixin):
    __tablename__ = 'interview_individual_questions'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    question_text = sa.Column(sa.Text, nullable=False)
    resume_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            'hr_assistant_tasks.id',
            ondelete='CASCADE'
        )
    )
