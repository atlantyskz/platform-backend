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

class CloneController:

    def __init__(self,session:AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.assistant_session_repo = AssistantSessionRepository(session)
        self.assistant_repo = AssistantRepository(session)
        self.organization_repo = OrganizationRepository(session)

    async def save_video(self,user_id:int,text:str,agreement_video:UploadFile,sample_video:UploadFile):
        try:
            user = await self.user_repo.get_by_user_id(user_id)
            if user is None:
                raise NotFoundException('User not found')
            
        except Exception as e:
            raise e
