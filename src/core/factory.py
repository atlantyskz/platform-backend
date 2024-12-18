from fastapi import Depends
from src.controllers.auth import AuthController
from src.controllers.hr_agent import HRAgentController
from src.controllers.organization import OrganizationController
from src.controllers.organization_member import OrganizationMemberController
from src.core.databases import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.extractor import get_thread_pool
from src.core.backend import BackgroundTasksBackend
from src.services.extractor import AsyncTextExtractor,get_thread_pool,get_text_extractor

class Factory:


    def get_auth_controller(session:AsyncSession = Depends(get_session)):
        return AuthController(
            session
        )

    def get_hr_agent_controller(
        session:AsyncSession = Depends(get_session),
        text_extractor: AsyncTextExtractor = Depends(get_text_extractor)
        ):
        return HRAgentController(
            session,
            text_extractor
        )
    
    def get_organization_controller(session: AsyncSession = Depends(get_session)):
        return OrganizationController(
            session
        )
    
    def get_org_member_controller(session: AsyncSession = Depends(get_session)):
        return OrganizationMemberController(session)
                                                                                    
    def get_bg_backend(session: AsyncSession = Depends(get_session)) -> BackgroundTasksBackend:
            return BackgroundTasksBackend(session)