import uuid
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.permission import user_permissions

class Vacancy(Base,TimestampMixin):

    __tablename__ = 'vacancy'

    id: so.Mapped[uuid.UUID] = so.mapped_column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id: so.Mapped[uuid.UUID] = so.mapped_column(
        sa.ForeignKey('assistant_sessions.id', ondelete='CASCADE'),
        nullable=False
    )
    title:so.Mapped[str] = so.mapped_column(sa.String(50),nullable=False)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False)
    vacancy_text: so.Mapped[dict] = so.mapped_column(sa.JSON, nullable=True)
    is_archived: so.Mapped[bool] = so.mapped_column(sa.Boolean,default=False, nullable=True)

    user = so.relationship(
        "User",back_populates='user_vacancies',
    )
    session = so.relationship(
        "AssistantSession",back_populates='vacancies'
    )
