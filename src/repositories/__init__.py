from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


from .whatsapp_instance import WhatsappInstanceRepository
from .cash_balance import CashBalanceRepository
from .organization_subscription import OrganizationSubscriptionRepository
from .balance import BalanceRepository
from .promocode import PromoCodeRepository
from .user import UserRepository
from .clone import CloneRepository
from .role import RoleRepository
from .vacancy_requirement import VacancyRequirementRepository
from .user_feedback import UserFeedbackRepository
from .assistant import AssistantRepository
from .refund_application import RefundApplicationRepository
from .organization_member import OrganizationMemberRepository
from .interview_individual_question import InterviewIndividualQuestionRepository
from .interview_common_question import InterviewCommonQuestionRepository
from .hh import HHAccountRepository
from .favorite_resume import FavoriteResumeRepository
from .discount import DiscountRepository
from .chat_message_history import ChatHistoryMessageRepository
from .billing_transactions import BillingTransactionRepository
from .bank_cards import BankCardRepository
from .balance_usage import BalanceUsageRepository
from .assistant_session import AssistantSessionRepository
from .organization import OrganizationRepository
from .subscription_plan import SubscriptionPlanRepository
from .whatsapp_instance_association import WhatsappInstanceAssociationRepository
from .whatsapp_instance import WhatsappInstanceDTO
from .whatsapp_instance_association import WhatsappInstanceAssociation
from .whatsapp_instance import InstanceTypeEnum
from .current_whatsapp_instance import CurrentWhatsappInstanceRepository
from .user_interaction_repository import UserInteractionRepository

__all__ = [
    "WhatsappInstanceRepository",
    "CashBalanceRepository",
    "OrganizationSubscriptionRepository",
    "BalanceRepository",
    "PromoCodeRepository",
    "UserRepository",
    "CloneRepository",
    "RoleRepository",
    "VacancyRequirementRepository",
    "UserFeedbackRepository",
    "AssistantSessionRepository",
    "InterviewIndividualQuestionRepository",
    "InterviewCommonQuestionRepository",
    "HHAccountRepository",
    "FavoriteResumeRepository",
    "BankCardRepository",
    "BalanceRepository",
    "BillingTransactionRepository",
    "OrganizationMemberRepository",
    "OrganizationRepository",
    "SubscriptionPlanRepository",
    "WhatsappInstanceAssociationRepository",
    "CurrentWhatsappInstanceRepository",
    "UserInteractionRepository",
]
