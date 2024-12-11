import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base
from src.models.role import role_permissions


user_permissions = sa.Table(
    'user_permissions',
    Base.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
    sa.Column('permission_id', sa.Integer, sa.ForeignKey('permissions.id'), primary_key=True),
)


class Permission(Base):
    __tablename__ = 'permissions'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, unique=True)
    
    roles = so.relationship(
        'Role', secondary=role_permissions, back_populates='permissions'
    )
    users = so.relationship(
        'User', 
        secondary=user_permissions, 
        back_populates='permissions'
    )