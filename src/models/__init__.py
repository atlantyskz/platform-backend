from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base, mapped_column


class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return mapped_column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        )


Base = declarative_base()

from .role import RoleEnum

from .user import User
from .permission import Permission, role_permissions
from .role import Role, role_permissions
from .organization import Organization
from .assistant import Assistant
from .organization_member import OrganizationMember
from .hr_assistant_task import HRTask
from .assistant_session import AssistantSession
from .assigned_assistant import assigned_assistant
from .vacancy import Vacancy
from .favorite_resume import FavoriteResume
from .vacancy_requirement import VacancyRequirement
from .chat_message_history import ChatMessageHistory
from .user_feedback import UserFeedback
from .billing_transactions import BillingTransaction
from .balance import Balance
from .discount import Discount
from .balance_usage import BalanceUsage
from .refund_application import RefundApplication
from .hh import HHAccount
from .interview_common_question import InterviewCommonQuestion
from .interview_individual_question import InterviewIndividualQuestion

from .promocode import PromoCode
from .subscription_plan import SubscriptionPlan
from .organization_subscription import OrganizationSubscription
from .cash_balance import CashBalance
from .bank_cards import BankCard
from .whatsapp_instance import WhatsappInstance
from .current_whatsapp_instance import CurrentWhatsappInstance
from .whatsapp_instance import user_instance_association
from .user_interaction import UserInteraction
from .question_generate_session import QuestionGenerateSession
from .question_generate_session import GenerateStatus

sql_admin_models_list = [
    User,
    Role,
    Organization,
    OrganizationMember,
    Assistant,
    HRTask,
    AssistantSession,
    Vacancy,
    FavoriteResume,
    VacancyRequirement,
    ChatMessageHistory,
    UserFeedback,
    BillingTransaction,
    Balance,
    Discount,
    BalanceUsage,
    RefundApplication,
    HHAccount,
    InterviewCommonQuestion,
    InterviewIndividualQuestion,
    PromoCode,
    SubscriptionPlan,
    OrganizationSubscription,
    CashBalance,
    BankCard,
    WhatsappInstance,
    CurrentWhatsappInstance,
    UserInteraction,
    QuestionGenerateSession
]
