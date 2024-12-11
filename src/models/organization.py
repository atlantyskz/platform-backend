import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin

class Organization(Base,TimestampMixin):

    __tablename__ = 'organizations'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    name: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    contact_information:so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    registered_address:so.Mapped[str] = so.mapped_column(sa.String,nullable=False)


    members = so.relationship(
        "OrganizationMember",
        back_populates='organization',
        cascade="all, delete-orphan",
        passive_deletes=True
    )