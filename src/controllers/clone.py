import csv
import json
from io import StringIO
from uuid import uuid4
from typing import List, Optional

from fastapi import UploadFile
from src.services.helpers import generate_clone_filekey
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
            bucket_name="clone-files"
        )
        self.user_repo = UserRepository(session)
        self.assistant_session_repo = AssistantSessionRepository(session)
        self.assistant_repo = AssistantRepository(session)
        self.organization_repo = OrganizationRepository(session)
        self.clone_repo = CloneRepository(session)


    async def create_clone(
            self,
            user_id: int,
            lipsynch_text: str,
            agreement_video: UploadFile,
            sample_video: UploadFile
        ) -> dict:
            async with self.session.begin():
                try:
                    # Генерация уникального идентификатора сессии
                    session_id = str(uuid4())

                    # Чтение данных файлов
                    agreement_video_data = await agreement_video.read()
                    sample_video_data = await sample_video.read()

                    # Генерация уникальных ключей для каждого файла
                    agreement_video_key = generate_clone_filekey(session_id, agreement_video.filename)
                    sample_video_key = generate_clone_filekey(session_id, sample_video.filename)

                    # Загрузка файлов в MinIO через upload_single_file
                    agreement_uploaded = await self.minio_uploader.upload_single_file(agreement_video_data, agreement_video_key)
                    sample_uploaded = await self.minio_uploader.upload_single_file(sample_video_data, sample_video_key)

                    # Извлечение относительных путей (например, "clone-files/filename.mp4")
                    agreement_video_path = agreement_uploaded[0]
                    sample_video_path = sample_uploaded[0]

                    # Создание записи клона в базе данных
                    await self.clone_repo.create_clone({
                        'user_id': user_id,
                        'agreement_video_path': agreement_video_key,
                        'sample_video_path': sample_video_key,
                        'lipsynch_text': lipsynch_text,
                        'status': 'pending'
                    })

                    return {
                        'message': "Successfully uploaded",
                        'status': 'pending'
                    }

                except Exception as e:
                    raise BadRequestException(f"Error creating clone: {str(e)}")
    

    async def get_all_clone_requests(self,):
        async with self.session.begin():
            all = await self.clone_repo.get_all()
            return all
        
    async def get_request_by_id(self,id):
        async with self.session.begin():
            request = await self.clone_repo.get_clone_by_id(id)
            return request

    async def get_video_by_id(self,id,type_v):
        if type_v =='agreement':
            