
from enum import Enum
import sqlalchemy as sa
import sqlalchemy.orm as so

from src.models import Base,TimestampMixin

class UserFeedback(Base,TimestampMixin):
    __tablename__  = 'user_feedbacks'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True)
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id'),nullable=False)
    user_email: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    user_organization: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)
    experience_rating: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False)  # Оценка опыта использования сайта
    vacancy_creation_rating: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False)  # Оценка создания вакансии
    resume_analysis_rating: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False)  # Оценка анализа резюме
    improvements: so.Mapped[str | None] = so.mapped_column(sa.Text, nullable=True)  # Что улучшить
    vacancy_price: so.Mapped[str | None] = so.mapped_column(sa.Text, nullable=True)  # Цена за генерацию одной вакансии
    resume_analysis_price: so.Mapped[str | None] = so.mapped_column(sa.Text, nullable=True)  # Цена за анализ 100 резюме
    free_comment: so.Mapped[str | None] = so.mapped_column(sa.Text, nullable=True)  # Свободный комментарий

    user = so.relationship("User",back_populates='user_feedbacks')
    def __str__(self):
        return self.id