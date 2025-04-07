from sqlalchemy.ext.asyncio import AsyncSession

from src import repositories
from src.core import exceptions


class AssistantController:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = repositories.UserRepository(session)
        self.assistant_session_repo = repositories.AssistantSessionRepository(session)
        self.assistant_repo = repositories.AssistantRepository(session)
        self.organization_repo = repositories.OrganizationRepository(session)

    async def add_assistant_to_organization(self, user_id: int, assistant_id: int):
        try:
            async with self.session.begin():
                user_organization, assistant,org_assistant = await self._get_organization_assistant(
                    user_id,
                    assistant_id
                )
                print(org_assistant)
                if org_assistant:
                    raise exceptions.BadRequestException("This assistant is already added to your organization")
                await self.assistant_repo.add_assistant_to_organization(user_organization.id, assistant.id)
                await self.session.commit()
            return {
                'success': True
            }
        except Exception:
            raise

    async def delete_from_organization(self, user_id: int, assistant_id: int):
        try:
            async with self.session.begin():
                user_organization, assistant, org_assistant = await self._get_organization_assistant(
                    user_id,
                    assistant_id
                )
                if org_assistant is None:
                    raise exceptions.BadRequestException("This assistant is not in your organization")
                result = await self.assistant_repo.delete_assigned_assistant(user_organization.id, assistant.id)
                if result == 0:
                    raise exceptions.BadRequestException("Assistant not assigned to this organization")
                await self.session.commit()
            return {
                'success': True
            }
        except Exception:
            await self.session.rollback()
            raise

    async def get_all_assistants(self):
        return await self.assistant_repo.get_all_assistants()

    async def _get_organization_assistant(self, user_id: int, assistant_id: int):
        user_organization = await self.organization_repo.get_user_organization(user_id)
        if user_organization is None:
            raise exceptions.BadRequestException("You dont have organization")
        assistant = await self.assistant_repo.get_assistant_by_id(assistant_id)
        if assistant is None:
            raise exceptions.BadRequestException('Assistant not found')
        org_assistant = await self.assistant_repo.get_org_assistant(
            user_organization.id, assistant.id
        )
        return user_organization, assistant, org_assistant
