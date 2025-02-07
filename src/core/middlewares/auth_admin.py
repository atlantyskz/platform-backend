from fastapi import Depends
from starlette.requests import Request
from src.core.password import PasswordHandler
from src.repositories.user import UserRepository
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.databases import session_manager



import secrets
from typing import Callable, AsyncIterator, AsyncContextManager
from starlette.requests import Request
from sqladmin.authentication import AuthenticationBackend
from src.repositories.user import UserRepository
from src.core.password import PasswordHandler
from sqlalchemy.ext.asyncio import AsyncSession

class AdminAuth(AuthenticationBackend):
    def __init__(self,secret_key: str):
        super().__init__(secret_key)
        self.session_manager = session_manager

    async def login(self, request: Request) -> bool:
    
        form = await request.form()
        email = form.get("username")
        password = form.get("password")
        if not email or not password:
            return False
        async with self.session_manager.session() as session:
            user_repository = UserRepository(session)
            user = await user_repository.get_by_email(email)
            if user is None or not PasswordHandler.verify(user.password, password) or user.role.name != 'super_admin':
                return False

            token = secrets.token_urlsafe(32)
            request.session.update({
                "token": token,
                "user_id": user.id,
            })
            return True

    async def logout(self, request: Request) -> bool:
        """
        Очистка сессии при логауте.
        """
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """
        Проверка аутентификации: здесь можно проводить дополнительные проверки,
        например, сверять token, проверять существование пользователя и т.д.
        """
        token = request.session.get("token")
        return bool(token)



authentication_backend = AdminAuth(secret_key="secret")
