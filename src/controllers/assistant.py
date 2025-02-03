import csv
import json
from io import StringIO
from uuid import uuid4
from typing import List, Optional
from fastapi import  UploadFile, WebSocket
from fastapi.responses import StreamingResponse
from src.core.exceptions import BadRequestException,NotFoundException
from src.repositories.assistant_session import AssistantSessionRepository
from src.repositories.assistant import AssistantRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.favorite_resume import FavoriteResumeRepository
from src.repositories.vacancy import VacancyRepository
from src.repositories.user import UserRepository
from src.core.exceptions import BadRequestException
from src.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.backend import BackgroundTasksBackend
from src.services.extractor import AsyncTextExtractor
from src.services.request_sender import RequestSender

class AssistantController:

    def __init__(self,session:AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.assistant_session_repo = AssistantSessionRepository(session)
        self.assistant_repo = AssistantRepository(session)
        self.organization_repo = OrganizationRepository(session)

    async def add_assistant_to_organization(self,user_id:int, assistant_id:int):
        try:
            async with self.session.begin(): 
                user_organization = await self.organization_repo.get_user_organization(user_id)
                if user_organization is None:
                    raise BadRequestException("You dont have organization")
                assistant = await self.assistant_repo.get_assistant_by_id(assistant_id)
                if assistant is None:
                    raise BadRequestException('Assistant not found')
                org_assistant = await self.assistant_repo.get_org_assistant(
                    user_organization.id, assistant.id  
                )
                if org_assistant:
                    raise BadRequestException("This assistant is already added to your organization")
                await self.assistant_repo.add_assistant_to_organization(user_organization.id,assistant.id)
                await self.session.commit()
            return {
                'success':True
            }                                                                                               
        except Exception:                                                                                                                           
            raise 

    async def delete_from_organization(self, user_id:int, assistant_id:int):
        try:
            async with self.session.begin(): 
                user_organization = await self.organization_repo.get_user_organization(user_id)
                if user_organization is None:
                    raise BadRequestException("You dont have organization")
                assistant = await self.assistant_repo.get_assistant_by_id(assistant_id)
                if assistant is None:
                    raise BadRequestException('Assistant not found')
                org_assistant = await self.assistant_repo.get_org_assistant(
                    user_organization.id, assistant.id  
                )   
                if org_assistant is None:
                    raise BadRequestException("This assistant is not in your organization")
                result = await self.assistant_repo.delete_assigned_assistant(user_organization.id,assistant.id)
                if result == 0:
                    raise BadRequestException("Assistant not assigned to this organization")
                await self.session.commit()
            return {
                'success':True
            }                                                                                               
        except Exception:
            await self.session.rollback()                                                                                                                           
            raise 

    async def get_all_assistants(self):

        assistants = await self.assistant_repo.get_all_assistants()
        
        return assistants