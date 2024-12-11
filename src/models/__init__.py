import os
from sqlalchemy.orm import declarative_base,mapped_column
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr


class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return mapped_column(DateTime, default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return mapped_column(
            DateTime,
            default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


Base = declarative_base()
from .permission import Permission,role_permissions
from .role import Role,role_permissions
from .organization import Organization
from .organization_member import OrganizationMember
from .user import User