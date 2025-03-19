from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.assistant import AssistantController
from src.controllers.auth import AuthController
from src.controllers.balance import BalanceController
from src.controllers.billing import BillingController
from src.controllers.clone import CloneController
from src.controllers.hh import HHController
from src.controllers.hr_agent import HRAgentController
from src.controllers.interview_common_question import InterviewCommonQuestionController
from src.controllers.interview_individual_question import InterviewIndividualQuestionController
from src.controllers.organization import OrganizationController
from src.controllers.organization_member import OrganizationMemberController
from src.controllers.user_feedback import UserFeedbackController
from src.core.backend import BackgroundTasksBackend
from src.core.databases import get_session
from src.services.extractor import AsyncTextExtractor, get_text_extractor


class Factory:

    def get_auth_controller(session: AsyncSession = Depends(get_session)) -> AuthController:
        return AuthController(
            session
        )

    def get_hr_agent_controller(
            session: AsyncSession = Depends(get_session),
            text_extractor: AsyncTextExtractor = Depends(get_text_extractor)
    ) -> HRAgentController:
        return HRAgentController(
            session,
            text_extractor
        )

    def get_organization_controller(session: AsyncSession = Depends(get_session)) -> OrganizationController:
        return OrganizationController(
            session
        )

    def get_org_member_controller(session: AsyncSession = Depends(get_session)) -> OrganizationMemberController:
        return OrganizationMemberController(
            session
        )

    def get_bg_backend(session: AsyncSession = Depends(get_session)) -> BackgroundTasksBackend:
        return BackgroundTasksBackend(
            session
        )

    def get_assistant_controller(session: AsyncSession = Depends(get_session)) -> AssistantController:
        return AssistantController(
            session
        )

    def get_user_feedback_controller(session: AsyncSession = Depends(get_session), ) -> UserFeedbackController:
        return UserFeedbackController(
            session
        )

    def get_balance_controller(session: AsyncSession = Depends(get_session)) -> BalanceController:
        return BalanceController(
            session
        )

    def get_billing_controller(session: AsyncSession = Depends(get_session)) -> BillingController:
        return BillingController(
            session
        )

    def get_hh_controller(session: AsyncSession = Depends(get_session)) -> HHController:
        return HHController(
            session
        )

    def get_clone_controller(session: AsyncSession = Depends(get_session)) -> CloneController:
        return CloneController(
            session
        )

    def get_common_question_controller(
            session: AsyncSession = Depends(get_session)) -> InterviewCommonQuestionController:
        return InterviewCommonQuestionController(session)

    def get_individual_question_controller(
            session: AsyncSession = Depends(get_session)) -> InterviewIndividualQuestionController:
        return InterviewIndividualQuestionController(session)
