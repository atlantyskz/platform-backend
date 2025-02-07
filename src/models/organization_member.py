import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin


class OrganizationMember(Base,TimestampMixin):
    __tablename__ = 'organization_members'


    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id',ondelete="CASCADE"),nullable=False)
    organization_id:so.Mapped[int] = so.mapped_column(sa.ForeignKey('organizations.id',ondelete="CASCADE"),nullable=False)
    role_alias: so.Mapped[str] = so.mapped_column(sa.String(50),nullable=False)
    
    user = so.relationship(
        "User",back_populates='members',
    )
    
    organization = so.relationship("Organization", back_populates="members") 

    def __str__(self):
        return f"{self.id}"