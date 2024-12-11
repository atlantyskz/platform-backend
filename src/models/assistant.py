import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin

class Assistant(Base,TimestampMixin):

    __tablename__ = 'assistants'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    name: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    type: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)

    members = so.relationship(
        "OrganizationMember",
        back_populates='organization',
        cascade="all, delete-orphan",
        passive_deletes=True
    )