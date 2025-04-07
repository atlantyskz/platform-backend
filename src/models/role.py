from enum import Enum

import sqlalchemy as sa
import sqlalchemy.orm as so

from src.models import Base, TimestampMixin

role_permissions = sa.Table(
    'role_permissions',
    Base.metadata,
    sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id'), primary_key=True),
    sa.Column('permission_id', sa.Integer, sa.ForeignKey('permissions.id'), primary_key=True),
)


class Role(Base, TimestampMixin):
    __tablename__ = 'roles'

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    permissions = so.relationship(
        'Permission', secondary=role_permissions, back_populates='roles'
    )
    users = so.relationship(
        "User", back_populates="role"
    )

    def __str__(self):
        return self.name


class RoleEnum(str, Enum):
    SUPER_ADMIN = 'super_admin'
    ADMIN = 'admin'
    EMPLOYER = 'employer'
