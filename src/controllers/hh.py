import asyncio
import time
import httpx
import logging
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List
from urllib.parse import urlencode

from fastapi import WebSocket
from fastapi.responses import RedirectResponse

import math

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

_resume_cache: Dict[str, dict] = {}

# Ограничитель одновременных запросов – максимум 5 параллельных запросов
CONCURRENCY_LIMIT = 5
semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


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

    async def get_auth_url(self):
        params = {
            "response_type": "code",
            "client_id": settings.CLIENT_ID,
            "redirect_uri": "https://platform.atlantys.kz/assistants/hr/hh",
        }
        auth_url = f"https://hh.ru/oauth/authorize?{urlencode(params)}"
        return RedirectResponse(auth_url)

    async def auth_callback(self, user_id: int, code: str) -> dict:
        """
        Обработка callback-запроса успешной OAuth-авторизации в HH.
        Производится обмен кода на access и refresh токены, вычисляется время истечения
        и данные сохраняются в БД.
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
    
    async def get_user_vacancies(self, user_id: int, status: str, page_from: int) -> dict:
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

        # Собираем все вакансии всех менеджеров в один список
        all_vacancies = []
        async with httpx.AsyncClient() as client:
            for manager in managers:
                manager_id = manager.get("id")
                page_number = 0  # Начинаем с первой страницы для каждого менеджера
                
                while True:
                    try:
                        # Получаем вакансии для текущей страницы менеджера"
                        try:
                            vacancies_response = await client.get(
                                f"https://api.hh.ru/employers/{emp_id}/vacancies/{status}?page={page_number}&manager_id={manager_id}",
                                headers=headers,
                                timeout=10.0,
                            )
                        except httpx.RequestError as exc:
                            pass
                            print(f"HTTP error during vacancies retrieval: {exc}")
                        print(vacancies_response.json())
                        vacancies_data = vacancies_response.json()
                        vacancies = vacancies_data.get("items", [])
                        
                        # Если вакансий нет, выходим из цикла
                        if not vacancies:
                            break

                        # Добавляем вакансии текущей страницы в общий список
                        all_vacancies.extend(vacancies)

                        # Если на текущей странице меньше вакансий, чем на максимальной, выходим из цикла
                        if len(vacancies) < vacancies_data.get("per_page", 10):
                            break

                        # Переходим на следующую страницу
                        page_number += 1
                    except httpx.RequestError as exc:
                        raise BadRequestException(f"HTTP error during vacancies retrieval for manager {manager_id}: {exc}") from exc

        # Пагинация для всех вакансий
        items_per_page = 10
        total_items = len(all_vacancies)
        total_pages = math.ceil(total_items / items_per_page)

        # Вычисляем индексы для среза
        start_index = (page_from - 1) * items_per_page
        end_index = start_index + items_per_page

        # Получаем вакансии для текущей страницы
        paginated_vacancies = all_vacancies[start_index:end_index]

        result = {
            "vacancies": paginated_vacancies,
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page_from,
            'items_per_page':len(paginated_vacancies)
        }
        return result

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
            return {"message": "Logged out"}
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
        return {"message": "Token refreshed"}

    async def get_hh_account_info(self, user_id: int) -> dict:
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise NotFoundException("HH account not found")
        if datetime.utcnow() >= hh_account.expires_at - timedelta(minutes=5):
            hh_account = await self.refresh_token(user_id)
        headers = {"Authorization": f"Bearer {hh_account.access_token}"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("https://api.hh.ru/me", headers=headers, timeout=10.0)
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during account info retrieval: {exc}") from exc
        if response.status_code == 401:
            hh_account = await self.refresh_token(user_id)
            headers = {"Authorization": f"Bearer {hh_account.access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.hh.ru/me", headers=headers)
        if response.status_code != 200:
            raise BadRequestException(f"Error retrieving HH account info: {response.text}")
        return response.json()

    async def get_vacancy_by_id(self, user_id: int, vacancy_id: int) -> dict:
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise NotFoundException("HH account not found")
        if datetime.utcnow() >= hh_account.expires_at - timedelta(minutes=5):
            hh_account = await self.refresh_token(user_id)
        headers = {"Authorization": f"Bearer {hh_account.access_token}"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"https://api.hh.ru/vacancies/{vacancy_id}",
                                              headers=headers, timeout=10.0)
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during vacancy retrieval: {exc}") from exc
        return response.json()

    async def get_vacancy_applicants(self, user_id: int, vacancy_id: int) -> dict:
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
                    headers=headers, timeout=10.0)
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during applicants retrieval: {exc}") from exc
        if response.status_code != 200:
            raise BadRequestException(f"Error retrieving applicants: {response.text}")
        return response.json()

    async def get_all_applicant_resume_ids(self, user_id: int, vacancy_id: int, per_page: int = 25) -> list:
        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise Exception("HH account not found")
        headers = {"Authorization": f"Bearer {hh_account.access_token}"}
        all_resume_ids = []
        page = 0
        async with httpx.AsyncClient() as client:
            while True:
                url = f"https://api.hh.ru/negotiations/response?vacancy_id={vacancy_id}&page={page}&per_page={per_page}"
                response = await client.get(url, headers=headers, timeout=10.0)
                if response.status_code != 200:
                    break
                data = response.json()
                items = data.get("items", [])
                if not items:
                    break 
                resume_ids = [item.get("resume", {}).get("id") for item in items if item.get("resume", {}).get("id")]
                all_resume_ids.extend(resume_ids)
                page += 1
        return all_resume_ids

    async def fetch_resume_details(self, user_id: int, resume_id: str) -> dict:
        """
        Получение полного резюме кандидата по его resume_id с обработкой rate limiting.
        Используется экспоненциальный бэкофф, кэширование и ограничение одновременных запросов.
        """
        if resume_id in _resume_cache:
            return _resume_cache[resume_id]

        hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
        if hh_account is None:
            raise Exception("HH account not found")
        headers = {"Authorization": f"Bearer {hh_account.access_token}"}
        url = f"https://api.hh.ru/resumes/{resume_id}"
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            async with semaphore:
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get(url, headers=headers, timeout=10.0)
                    except httpx.RequestError as exc:
                        raise Exception(f"HTTP error during resume retrieval: {exc}") from exc

            if response.status_code == 200:
                data = response.json()
                _resume_cache[resume_id] = data
                return data
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = int(retry_after) if retry_after and retry_after.isdigit() else (2 ** retry_count)
                logging.warning(f"Ошибка 429 для resume_id {resume_id}. Ретрай через {delay} секунд (попытка {retry_count+1}/{max_retries})")
                await asyncio.sleep(delay)
                retry_count += 1
            else:
                raise Exception(f"Error retrieving resume {resume_id}: {response.text}")
        raise Exception(f"Превышено число попыток для resume {resume_id}")

    async def analyze_vacancy_applicants(self, session_id: str, user_id: int, vacancy_id: int) -> dict:
        start_time = time.time()
        logging.info(f"Запуск анализа вакансии. session_id={session_id}, user_id={user_id}, vacancy_id={vacancy_id}")
        async with self.session.begin():
            session = await self.assistant_session_repo.get_by_session_id(session_id)
            if session is None:
                logging.error(f"Сессия не найдена: session_id={session_id}")
                raise NotFoundException("Session not found")
            logging.debug(f"Найдена сессия: {session}")
            hh_account = await self.hh_account_repository.get_hh_account_by_user_id(user_id)
            if hh_account is None:
                logging.error(f"HH аккаунт не найден для user_id={user_id}")
                raise NotFoundException("HH account not found")
            logging.debug(f"Получен HH аккаунт: {hh_account}")

            user_organization = await self.organization_repo.get_user_organization(user_id)
            logging.debug(f"Организация пользователя: {user_organization}")

            now = datetime.utcnow()
            if now >= hh_account.expires_at - timedelta(minutes=5):
                logging.info(f"Токен скоро истекает, обновление для user_id={user_id}")
                hh_account = await self.refresh_token(user_id)
                logging.debug(f"Токен обновлён: {hh_account}")
            else:
                logging.debug("Токен еще действителен")

            vacancy_raw = await self.get_vacancy_by_id(user_id, vacancy_id)
            vacancy_text = extract_vacancy_summary(vacancy_raw)
            logging.info(f"Извлечён текст вакансии (первые 100 символов): {vacancy_text[:100]}")

            balance = await self.balance_repo.get_balance(user_organization.id)
            logging.debug(f"Баланс пользователя: {balance}")
            if balance.atl_tokens < 5:
                logging.error(f"Недостаточно средств: имеется {balance.atl_tokens} токенов, требуется минимум 5")
                raise BadRequestException("Insufficient balance")
            logging.info(f"Баланс достаточен: {balance.atl_tokens} токенов")

            skipped_resumes = []
            all_task_ids = []

            resume_ids = await self.get_all_applicant_resume_ids(user_id, vacancy_id)
            logging.info(f"Найдено {len(resume_ids)} ID резюме")
            if not resume_ids:
                logging.warning("Нет резюме для обработки")
                return {
                    "session_id": session_id,
                    "tasks": [],
                    "skipped_resumes": [],
                    "task_count": 0
                }

            logging.info("Запуск параллельного получения деталей резюме")
            tasks = [self.fetch_resume_details(user_id, resume_id) for resume_id in resume_ids]
            resumes_data = await asyncio.gather(*tasks, return_exceptions=True)
            logging.debug("Детали резюме получены")

            for resume_id, resume_data in zip(resume_ids, resumes_data):
                if isinstance(resume_data, Exception):
                    logging.error(f"Ошибка при получении резюме {resume_id}: {resume_data}")
                    skipped_resumes.append(resume_id)
                    continue

                candidate_info = extract_full_candidate_info(resume_data)
                candidate_resume_text = assemble_candidate_summary(candidate_info)
                if not candidate_resume_text:
                    logging.warning(f"Пустой текст резюме кандидата для resume_id={resume_id}")
                    skipped_resumes.append(resume_id)
                    continue

                task_id = str(uuid.uuid4())
                logging.info(f"Создание фоновой задачи с id={task_id} для resume_id={resume_id}")
                await self.bg_backend.create_task({
                    "task_id": task_id,
                    "resume_id":resume_id,
                    "vacancy_id":vacancy_id,
                    "session_id": session_id,
                    "task_type": "hh cv analyze",
                    "task_status": "pending",
                    "hh_file_url": resume_data.get("download", {}).get("pdf", {}).get("url", None),
                })

                logging.info(f"Отправка задачи {task_id} на обработку через DramatiqWorker")
                DramatiqWorker.process_resume.send(
                    task_id,
                    vacancy_text,
                    candidate_resume_text,
                    user_id,
                    user_organization.id,
                    balance.id,
                    candidate_resume_text  # Здесь передается текст резюме (можно заменить на другой параметр)
                )
                all_task_ids.append(task_id)
                logging.info(f"Обработка резюме {resume_id} для user_id={user_id}")

            logging.info(f"Завершено создание задач: создано {len(all_task_ids)} задач, пропущено {len(skipped_resumes)} резюме")
            finish_time = time.time()
            print("TIME DIFF: ", finish_time - start_time)
            return {
                "session_id": session_id,
                "tasks": all_task_ids,
                "skipped_resumes": skipped_resumes,
                "task_count": len(all_task_ids)
            }

    async def websocket_endpoint(self, websocket: WebSocket, vacancy_id: str, message_from_server: dict):
        await websocket.accept()
        while True:
            await websocket.send_text(message_from_server)
