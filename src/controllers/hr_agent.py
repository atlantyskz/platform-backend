

from concurrent.futures import ThreadPoolExecutor
from multiprocessing.pool import ThreadPool
from typing import List, Optional
from uuid import uuid4
from fastapi import HTTPException, UploadFile
from pydantic import EmailStr
from sqlalchemy import select
from src.repositories.user import UserRepository
from src.controllers import BaseController
from src.models import User
from src.core.security import JWTHandler
from src.core.password import PasswordHandler
from src.core.exceptions import BadRequestException,UnauthorizedException
from src.schemas.responses.auth import Token
from src.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from src.core.settings import settings
from src.services.request_sender import RequestSender
from src.services.extractor import AsyncTextExtractor
import json
from src.services.ai_analyzer import FileHandlerService
from src.services.redis_service import RedisContextStorage

class HRAgentController:

    def __init__(self,session:AsyncSession,file_handler_service:FileHandlerService,context_storage:RedisContextStorage):
        self.session = session
        self.file_handler = file_handler_service
        self.context_storage = context_storage
        self.user_repo = UserRepository(session)

    async def create_vacancy(self, file: Optional[UploadFile], vacancy_text: Optional[str]):
        if file and file.filename == "":
            file = None

        if file and vacancy_text:
            raise BadRequestException("Only one of 'file' or 'vacancy_text' should be provided")
        
        if not file and not vacancy_text:
            raise BadRequestException("Either 'file' or 'vacancy_text' must be provided")
        
        user_message = None
        if file:
            content = await file.read()
            user_message = content.decode('utf-8')
        elif vacancy_text:
            user_message = vacancy_text

        response = await self.request_sender._send_request (
            llm_url=f'{settings.LLM_SERVICE_URL}/hr/generate_vacancy',
            json={"user_message": user_message}
        )
        return response
            

    async def cv_analyzer(self,context_id: Optional[str], vacancy_file: UploadFile, cv_files: List[UploadFile]):
        if context_id is None:
            context_id = str(uuid4())
        print(context_id)
        res = await self.file_handler.handle_files(context_id,vacancy_file,cv_files)
        return res
    
    async def get_cv_analyzer_result_by_context_id(self, context_id:str):
        res = await self.context_storage.get_task_results_by_context(context_id)
        return res
