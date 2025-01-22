import os
from sqlalchemy.orm import declarative_base,mapped_column
from sqlalchemy import DateTime, func
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
from .assistant import Assistant
from .organization_member import OrganizationMember
from .user import User
from .hr_assistant_task import HRTask
from .assistant_session import AssistantSession
from .assigned_assistant import assigned_assistant
from .vacancy import Vacancy
from .favorite_resume import FavoriteResume
from .vacancy_requirement import VacancyRequirement
from .chat_message_history import ChatMessageHistory