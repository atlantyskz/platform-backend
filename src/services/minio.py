from datetime import timedelta
import uuid
from minio import Minio
from minio.error import S3Error, InvalidResponseError
from fastapi import UploadFile
from typing import List, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import urllib.parse
from src.services.helpers import generate_file_key
import json
from io import BytesIO

from src.core.exceptions import BadRequestException

class MinioUploader:
    def __init__(self, host: str, access_key: str, secret_key: str, bucket_name: str, secure: bool = False):
        self.minio_client = Minio(
            host,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket_name = bucket_name
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.base_url = f"http://{host}" if not secure else f"https://{host}"

    async def upload_single_file(self, file_data: bytes, file_key: str) -> Tuple[str, str]:
        """Асинхронная загрузка одного файла"""
        try:
            # Конвертируем bytes в BytesIO
            data_stream = BytesIO(file_data)
            
            # Загружаем файл
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.minio_client.put_object(
                    self.bucket_name,
                    file_key,
                    data_stream,
                    len(file_data)
                )
            )
            
            # Формируем постоянный публичный URL
            permanent_url = f"{self.base_url}/{self.bucket_name}/{file_key}"
            print(permanent_url)
            
            return permanent_url, file_key

        except (S3Error, InvalidResponseError) as e:
            raise BadRequestException(f"Error uploading file to MinIO: {str(e)}")
        finally:
            # Закрываем BytesIO
            data_stream.close()


    async def ensure_bucket_exists(self):
        """Проверка и создание бакета при необходимости"""
        try:
            exists = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.minio_client.bucket_exists(self.bucket_name)
            )
            if not exists:
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: self.minio_client.make_bucket(self.bucket_name)
                )
                # Устанавливаем политику доступа для публичного чтения
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                        }
                    ]
                }
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: self.minio_client.set_bucket_policy(self.bucket_name, json.dumps(policy))
                )
        except S3Error as e:
            raise BadRequestException(f"Error setting up MinIO bucket: {str(e)}")

    async def save_files_in_minio(self, files: List[UploadFile], session_id: str) -> List[Tuple[str, str]]:
        """Параллельная загрузка множества файлов"""
        await self.ensure_bucket_exists()

        upload_tasks = []
        for file in files:
            try:
                file_data = await file.read()
                file_key = generate_file_key(session_id, file.filename)  # Генерация file key
                upload_tasks.append(self.upload_single_file(file_data, file_key))
            except Exception as e:
                raise BadRequestException(f"Error reading file {file.filename}: {str(e)}")

        return await asyncio.gather(*upload_tasks)


    def get_file(self, object_key: str) -> BytesIO:
            """
            Извлекает файл из MinIO и возвращает его как BytesIO.
            """
            try:
                response = self.minio_client.get_object(self.bucket_name, object_key)
                data = response.read()
                response.close()
                response.release_conn()
                return BytesIO(data)
            except S3Error as e:
                raise e