import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, List
from urllib.parse import urlencode
import uuid
from fastapi import WebSocket
from fastapi.responses import RedirectResponse
import httpx

from src.repositories.balance import BalanceRepository
from src.repositories.balance_usage import BalanceUsageRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.vacancy_requirement import VacancyRequirementRepository
from src.core.backend import BackgroundTasksBackend
from src.core.dramatiq_worker import DramatiqWorker
from src.repositories.favorite_resume import FavoriteResumeRepository
from src.repositories.vacancy import VacancyRepository
from src.repositories.assistant_session import AssistantSessionRepository
from src.repositories.assistant import AssistantRepository
from src.services.request_sender import RequestSender
from src.services.hh_extractor import assemble_candidate_summary, extract_full_candidate_info, extract_vacancy_summary
from src.core.exceptions import NotFoundException, BadRequestException
from src.repositories.user import UserRepository
from src.repositories.hh import HHAccountRepository
from src.core.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession


class HHController:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.hh_account_repository = HHAccountRepository(session)
        self.user_repository = UserRepository(session)
        self.request_sender = RequestSender()
        self.user_repo = UserRepository(session)
        self.favorite_repo = FavoriteResumeRepository(session)
        self.vacancy_repo = VacancyRepository(session)
        self.assistant_session_repo = AssistantSessionRepository(session)
        self.assistant_repo = AssistantRepository(session)
        self.bg_backend = BackgroundTasksBackend(session)
        self.organization_repo = OrganizationRepository(session)
        self.requirement_repo = VacancyRequirementRepository(session)
        self.balance_repo = BalanceRepository(session)
        self.balance_usage_repo = BalanceUsageRepository(session)


    async def get_auth_url(self,):
        params = {
            "response_type": "code",
            "client_id": settings.CLIENT_ID,
            "redirect_uri": "https://platform.atlantys.kz/assistants/hr/hh",
        }
        auth_url = f"https://hh.ru/oauth/authorize?{urlencode(params)}"
        return RedirectResponse(auth_url)

    async def auth_callback(self, user_id: int, code: str) -> dict:
        """
        Обработка callback-запроса  успешной OAuth-авторизации в HH.
        Производится обмен кода на access и refresh токены, вычисляется время истечения
        и данные сохраняются в БД.после
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "redirect_uri": "https://platform.atlantys.kz/assistants/hr/hh",
        }

        user = await self.user_repository.get_by_user_id(user_id)
        if user is None:
            raise NotFoundException("User not found")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.hh.ru/token", 
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0,
                )
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during token exchange: {exc}") from exc

        if response.status_code != 200:
            raise BadRequestException(f"Token exchange failed: {response.text}")

        response_data = response.json()
        access_token = response_data.get("access_token")
        refresh_token = response_data.get("refresh_token")
        expires_in = response_data.get("expires_in")
        if not (access_token and refresh_token and expires_in):
            raise BadRequestException("Incomplete token data received from HH")

        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        attributes = {
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }

        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            await self.hh_account_repository.create_hh_account(attributes)
        else:
            await self.hh_account_repository.update_hh_account(user_id, attributes)

        await self.session.commit()
        return {
            "message": "Authorization successful",
        }
    
    async def logout(self, user_id: int) -> dict:
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise NotFoundException("HH account not found")
        headers = {"Authorization": f"Bearer {hh_account.access_token}"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    "https://api.hh.ru/oauth/token",
                    headers=headers,
                    timeout=10.0,
                )
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during logout: {exc}") from exc
        if response.status_code == 204:
            await self.hh_account_repository.delete_hh_account(user_id)
            await self.session.commit()
            return {
                "message": "Logged out",
            }
        else:
            raise BadRequestException(f"Error during logout: {response.text}")


    async def refresh_token(self, user_id: int):
        """
        Обновление access_token с использованием refresh_token.
        Если токен протух или близок к истечению, производится запрос обновления у HH.
        """
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if not hh_account:
            raise NotFoundException("HH account not found")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": hh_account.refresh_token,
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.hh.ru/token",
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0,
                )
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during token refresh: {exc}") from exc

        if response.status_code != 200:
            raise BadRequestException(f"Error refreshing token: {response.text}")

        token_data = response.json()
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        new_attributes = {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": expires_at,
        }
        if not (new_attributes["access_token"] and new_attributes["refresh_token"]):
            raise BadRequestException("Incomplete token data received during refresh")

        await self.hh_account_repository.update_hh_account(user_id, new_attributes)
        await self.session.commit()
        return {
            "message": "Token refreshed",
        }

    async def get_hh_account_info(self, user_id: int) -> dict:
        """
        Получение информации об аккаунте HH.
        Перед выполнением запроса проверяется, не истёк ли access_token.
        Если срок действия истёк (или близок к истечению), производится автоматическое обновление.
        Затем выполняется запрос к защищённому эндпоинту HH.
        """
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise NotFoundException("HH account not found")

        # Если токен истёк или скоро истечёт (например, за 5 минут до истечения), обновляем
        if datetime.utcnow() >= hh_account.expires_at - timedelta(minutes=5):
            hh_account = await self.refresh_token(user_id)

        headers = {"Authorization": f"Bearer {hh_account.access_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.hh.ru/me",
                    headers=headers,
                    timeout=10.0,
                )
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during account info retrieval: {exc}") from exc

        # Если по какой-то причине получен 401, попробуем обновить токен и повторить запрос
        if response.status_code == 401:
            hh_account = await self.refresh_token(user_id)
            headers = {"Authorization": f"Bearer {hh_account.access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.hh.ru/me", headers=headers)

        if response.status_code != 200:
            raise BadRequestException(f"Error retrieving HH account info: {response.text}")

        return response.json()
    

async def get_user_vacancies(self, user_id: int, status: str | None, page: int) -> dict:
    """
    Получение списка вакансий пользователя на HH.
    """
    hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
    if hh_account is None:
        raise NotFoundException("HH account not found")

    if datetime.utcnow() >= hh_account.expires_at - timedelta(minutes=5):
        hh_account = await self.refresh_token(user_id)

    headers = {"Authorization": f"Bearer {hh_account.access_token}"}
    employer_data = await self.get_hh_account_info(user_id)
    emp_id = employer_data.get("employer", {}).get("id")
    print(emp_id)
    # Получаем список менеджеров
    async with httpx.AsyncClient() as client:
        try:
            managers_response = await client.get(
                f"https://api.hh.ru/employers/{emp_id}/managers", headers=headers, timeout=10.0
            )
            managers_response.raise_for_status()
            managers = managers_response.json().get("items", [])
        except httpx.RequestError as exc:
            raise BadRequestException(f"HTTP error during managers retrieval: {exc}") from exc

    vacancies = []
    async with httpx.AsyncClient() as client:
        for manager in managers:
            manager_id = manager.get("id")
            try:
                # Исправляем URL с пагинацией
                vacancies_response = await client.get(
                    f"https://api.hh.ru/employers/{emp_id}/vacancies/{status or 'active'}?page={page}&manager_id={manager_id}",
                    headers=headers,
                    timeout=10.0,
                )
                vacancies_response.raise_for_status()
                vacancies.extend(vacancies_response.json().get("items", []))
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during vacancies retrieval: {exc}") from exc

    return {"vacancies": vacancies}

    async def get_vacancy_by_id(self, user_id: int, vacancy_id: int) -> dict:
        """
        Получение информации о вакансии по её ID.
        """
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise NotFoundException("HH account not found")

        if datetime.utcnow() >= hh_account.expires_at - timedelta(minutes=5):
            hh_account = await self.refresh_token(user_id)

        headers = {"Authorization": f"Bearer {hh_account.access_token}"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://api.hh.ru/vacancies/{vacancy_id}",
                    headers=headers,
                    timeout=10.0,
                )
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during vacancy retrieval: {exc}") from exc            

        return response.json()
    
    async def get_vacancy_applicants(self, user_id: int, vacancy_id: int) -> dict:
        """
        Получение списка соискателей на вакансию.
        """
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise NotFoundException("HH account not found")

        if datetime.utcnow() >= hh_account.expires_at - timedelta(minutes=5):
            hh_account = await self.refresh_token(user_id)

        headers = {"Authorization": f"Bearer {hh_account.access_token}"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://api.hh.ru/negotiations/response?vacancy_id={vacancy_id}&page=2&per_page=50&age_to=25",
                    headers=headers,
                    timeout=10.0,
                )
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during applicants retrieval: {exc}") from exc

        if response.status_code != 200:
            raise BadRequestException(f"Error retrieving applicants: {response.text}")

        return response.json()
    
    async def analyze_vacancy(self,user_id:int,vacancy_id:int):
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise NotFoundException("HH account not found")
        if datetime.utcnow() >= hh_account.expires_at - timedelta(minutes=5):
            hh_account = await self.refresh_token(user_id)

        headers = {"Authorization": f"Bearer {hh_account.access_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://api.hh.ru/negotiations/response?vacancy_id=110202595&page=2&per_page=50&age_to=25",
                    headers=headers,
                    timeout=10.0,
                )
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during applicants retrieval: {exc}") from exc


    async def get_all_applicant_resume_ids(self, user_id: int, vacancy_id: int, per_page: int = 50, chunk_size: int = 50) -> AsyncGenerator[list, None]:
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise NotFoundException("HH account not found")

        # Обновляем токен, если требуется
        if datetime.utcnow() >= hh_account.expires_at - timedelta(minutes=5):
            hh_account = await self.refresh_token(user_id)

        headers = {"Authorization": f"Bearer {hh_account.access_token}"}
        page = 0
        current_chunk = []

        while True:
            url = f"https://api.hh.ru/negotiations/response?vacancy_id={vacancy_id}&page={page}&per_page={per_page}"
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(url, headers=headers, timeout=10.0)
                except httpx.RequestError as exc:
                    raise BadRequestException(f"HTTP error during applicants retrieval: {exc}") from exc

            if response.status_code != 200:
                raise BadRequestException(f"Error retrieving applicants: {response.text}")

            data = response.json()
            items = data.get("items", [])
            if not items:
                break

            for item in items:
                resume = item.get("resume", {})
                resume_id = resume.get("id")
                if resume_id:
                    current_chunk.append(resume_id)

                if len(current_chunk) >= chunk_size:
                    yield current_chunk
                    current_chunk = []

            if len(items) < per_page:
                break  # Все страницы обработаны
            page += 1

        # Если остались несданные резюме, отправляем их последним чанком
        if current_chunk:
            yield current_chunk    

    async def fetch_resume_details(self,user_id:int,resume_id:str,):
        url = f"https://api.hh.ru/resumes/{resume_id}"
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise NotFoundException("HH account not found")
        if datetime.utcnow() >= hh_account.expires_at - timedelta(minutes=5):
            hh_account = await self.refresh_token(user_id)
        headers = {"Authorization": f"Bearer {hh_account.access_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=10.0)
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during resume retrieval: {exc}") from exc

        if response.status_code != 200:
            raise BadRequestException(f"Error retrieving resume {resume_id}: {response.text}")
        return response.json()


    async def analyze_vacancy_applicants(self, session_id: str, user_id: int, vacancy_id: int) -> dict:
        """
        Анализирует отклики на вакансию. Запускает анализ резюме в фоновом режиме и возвращает список задач.
        """
        async with self.session.begin():
            session = await self.assistant_session_repo.get_by_session_id(session_id)
            if session is None:
                raise NotFoundException("Session not found")

            hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
            if hh_account is None:
                raise NotFoundException("HH account not found")

            user_organization = await self.organization_repo.get_user_organization(user_id)

            if datetime.utcnow() >= hh_account.expires_at - timedelta(minutes=5):
                hh_account = await self.refresh_token(user_id)

            vacancy_text = extract_vacancy_summary(await self.get_vacancy_by_id(user_id, vacancy_id))

            balance = await self.balance_repo.get_balance(user_organization.id)
            skipped_resumes = []
            all_task_ids = []
            if balance.atl_tokens < 5:
                raise BadRequestException("Insufficient balance")

            async for chunk in self.get_all_applicant_resume_ids(user_id, vacancy_id, chunk_size=50):
                for resume_id in chunk:
                    if balance.atl_tokens < 5:
                        skipped_resumes.append(resume_id)
                        continue  

                    resume_data = await self.fetch_resume_details(user_id, resume_id)
                    candidate_info = extract_full_candidate_info(resume_data)
                    resume_text = assemble_candidate_summary(candidate_info)

                    task_status = 'pending'
                    if not resume_text: 
                        task_status = 'error parsing'
                    else:
                        task_id = str(uuid.uuid4())
                        await self.bg_backend.create_task({
                            "task_id": task_id,
                            "session_id": session_id,
                            "task_type": "hh cv analyze",
                            "task_status": task_status,
                            "hh_file_url": resume_data.get("download", {}).get("pdf", {}).get("url", None),
                        })
                        if resume_text:
                            DramatiqWorker.process_resume.send(task_id, vacancy_text, resume_text, user_id, user_organization.id, balance.id, resume_text)
                            print(f"Processing resume {resume_id} for user {user_id}")
                            all_task_ids.append(task_id)
                    print(len(all_task_ids))
            return {"session_id": session_id, "tasks": all_task_ids, "skipped_resumes": skipped_resumes,'task_count':len(all_task_ids)}

    async def websocket_endpoint(self,websocket: WebSocket, vacancy_id: str,message_from_server:dict):
        await websocket.accept()
        
        while True:
            await websocket.send_text(message_from_server)