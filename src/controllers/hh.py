from datetime import datetime, timedelta
from urllib.parse import urlencode
from fastapi.responses import RedirectResponse
import httpx

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
        print(settings.CLIENT_ID)
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

        updated_hh_account = await self.hh_account_repository.update_hh_account(user_id, new_attributes)
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
    
    async def get_user_vacancies(self, user_id: int,status:str|None) -> dict:
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
        async with httpx.AsyncClient() as client:
            try:
                if status == 'archived':
                    response = await client.get(
                        f"https://api.hh.ru/employers/{emp_id}/vacancies/archived",
                        headers=headers,
                        timeout=10.0,
                    )
                else:
                    response = await client.get(
                        f"https://api.hh.ru/employers/{emp_id}/vacancies/active",
                        headers=headers,
                        timeout=10.0,
                    )
            except httpx.RequestError as exc:
                raise BadRequestException(f"HTTP error during vacancies retrieval: {exc}") from exc

        if response.status_code != 200:
            raise BadRequestException(f"Error retrieving user vacancies: {response.text}")

        return response.json()


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
    
