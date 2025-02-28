import csv
import json
from io import BytesIO, StringIO
import os
from uuid import uuid4
from typing import List, Optional

from fastapi import UploadFile
from fastapi.responses import StreamingResponse
import requests
from src.services.helpers import generate_clone_filekey
from src.core.exceptions import BadRequestException, NotFoundException
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

    def __init__(self, session: AsyncSession):
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
            gender:str,
            name:str,
            user_id: int,
            lipsynch_text: str,
            agreement_video: UploadFile,
            sample_video: UploadFile
        ) -> dict:
        async with self.session.begin():
            try:
                session_id = str(uuid4())

                agreement_video_data = await agreement_video.read()
                sample_video_data = await sample_video.read()

                agreement_video_key = generate_clone_filekey(session_id, agreement_video.filename)
                sample_video_key = generate_clone_filekey(session_id, sample_video.filename)

                agreement_uploaded = await self.minio_uploader.upload_single_file(agreement_video_data, agreement_video_key)
                sample_uploaded = await self.minio_uploader.upload_single_file(sample_video_data, sample_video_key)

                agreement_video_path = agreement_uploaded[0]
                sample_video_path = sample_uploaded[0]

                await self.clone_repo.create_clone({
                    'user_id': user_id,
                    'gender':gender,
                    'name':name,
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
    
    async def get_all_clone_requests(self):
        async with self.session.begin():
            all_requests = await self.clone_repo.get_all()
            return all_requests
        
    async def get_request_by_id(self,user_id:int, id):
        async with self.session.begin():
            request = await self.clone_repo.get_clone_by_id(id)
            if request.user_id != user_id:
                raise BadRequestException('User not found')
            
            return request
    
    async def get_clone_requests_by_user(self, user_id: int):
        async with self.session.begin():
            user_requests = await self.clone_repo.get_by_user(user_id)
            return user_requests
    

    async def stream_clone_video(self, user_id:int,clone_id: int, video_type: str) -> StreamingResponse:
        async with self.session.begin():
            clone_request = await self.clone_repo.get_clone_by_id(clone_id)
            if not clone_request:
                raise NotFoundException("Clone request not found")

            if video_type == 'agreement':
                video_key = clone_request.agreement_video_path
            elif video_type == 'sample':
                video_key = clone_request.sample_video_path
            else:
                raise BadRequestException("Invalid video type specified")

            video_stream = self.minio_uploader.get_file(video_key)
            if video_stream is None:
                raise NotFoundException("Video not found in storage")

            return StreamingResponse(video_stream, media_type="video/mp4")

    async def update_clone_request_status(self, clone_id: int, new_status: str, is_admin: bool) -> dict:
        
        async with self.session.begin():                
            updated_clone = await self.clone_repo.update_status(clone_id, new_status)

            if new_status.lower() == 'processing':
                # Скачиваем видео из MinIO
                agreement_video_data = self.minio_uploader.get_file(updated_clone.agreement_video_path)
                sample_video_data = self.minio_uploader.get_file(updated_clone.sample_video_path)
                headers = {
                    'X-API-SECRETID':os.getenv("X-API-SECRETID"),
                    'X-API-KEY':os.getenv("X-API-KEY")
                }
                files = {
                    "name": (None, updated_clone.name),
                    "gender": (None, updated_clone.gender),
                    "lipsynch_text": (None, updated_clone.lipsynch_text),
                    "agreement_video": ("agreement.mp4", BytesIO(agreement_video_data), "video/mp4"),
                    "sample_video": ("sample.mp4", BytesIO(sample_video_data), "video/mp4"),
                }

                return files

            if not updated_clone:
                raise NotFoundException("Clone request not found")
            
            return {
                'message': "Status updated successfully",
                'clone_id': clone_id,
                'new_status': new_status
            }