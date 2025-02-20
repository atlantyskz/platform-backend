import csv
import json
from io import StringIO
from uuid import uuid4
from typing import List, Optional

from fastapi import UploadFile
from src.core.exceptions import BadRequestException,NotFoundException
from src.repositories.assistant_session import AssistantSessionRepository
from src.repositories.assistant import AssistantRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.user import UserRepository
from src.core.exceptions import BadRequestException
from src.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.minio import MinioUploader
from src.repositories.clone import CloneRepository
class CloneController:

    def __init__(self,session:AsyncSession):
        self.session = session
        self.minio_uploader = MinioUploader(
            host="minio:9000",  
            access_key="admin",
            secret_key="admin123",
            bucket_name="clone_files"
        )
        self.user_repo = UserRepository(session)
        self.assistant_session_repo = AssistantSessionRepository(session)
        self.assistant_repo = AssistantRepository(session)
        self.organization_repo = OrganizationRepository(session)
        self.clone_repo = CloneRepository(session)


    async def create_clone(self, user_id: int, lipsynch_text: str, agreement_video: UploadFile, sample_video: UploadFile) -> dict:
        try:
            # Генерация уникального идентификатора для сессии
            session_id = f"{user_id}_{lipsynch_text}"

            # Загружаем видеофайлы в MinIO
            agreement_video_path, _ = await self.minio_uploader.upload_single_file(await agreement_video.read(), f"{session_id}_agreement.mp4")
            sample_video_path, _ = await self.minio_uploader.upload_single_file(await sample_video.read(), f"{session_id}_sample.mp4")

            # Создаем запись в базе данных
            clone = await self.clone_repo.create_clone({
                'user_id': user_id,
                'agreement_video_path': agreement_video_path,
                'sample_video_path': sample_video_path,
                'lipsynch_text': lipsynch_text,
                'status': 'pending'
            })
            return {
                'message':"Successfully uploaded",
                'status':'pending'
            }
        except Exception as e:
            raise BadRequestException(f"Error creating clone: {str(e)}")
