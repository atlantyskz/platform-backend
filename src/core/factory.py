from fastapi import Depends
from src.services.redis_service import get_redis_context_storage
from src.controllers.auth import AuthController
from src.controllers.hr_agent import HRAgentController
from src.controllers.organization import OrganizationController
from src.controllers.organization_member import OrganizationMemberController
from src.core.databases import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.extractor import get_thread_pool
from src.services.ai_analyzer import FileHandlerService, get_file_handler_service

class Factory:

    def get_auth_controller(session:AsyncSession = Depends(get_session)):
        return AuthController(
            session
        )

    def get_hr_agent_controller(
        session:AsyncSession = Depends(get_session),
        file_handler_service: FileHandlerService = Depends(get_file_handler_service),
        context_storage = Depends(get_redis_context_storage)
        ):
        return HRAgentController(
            session,
            file_handler_service,
            context_storage
        )
    
    def get_organization_controller(session: AsyncSession = Depends(get_session)):
        return OrganizationController(
            session
        )
    
    def get_org_member_controller(session: AsyncSession = Depends(get_session)):
        return OrganizationMemberController(session)