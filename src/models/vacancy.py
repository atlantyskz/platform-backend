import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.permission import user_permissions

class Vacancy(Base,TimestampMixin):

    __tablename__ = 'vacancy'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    title:so.Mapped[str] = so.mapped_column(sa.String(50),nullable=False)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False)
    vacancy_text: so.Mapped[dict] = so.mapped_column(sa.JSON, nullable=False)

    user = so.relationship(
        "User",back_populates='user_vacancies',
    )
    