

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from src.repositories.role import RoleRepository
from src.repositories.user import UserRepository
from src.controllers import BaseController
from src.models import User
from src.core.security import JWTHandler
from src.core.password import PasswordHandler
from src.core.exceptions import BadRequestException,UnauthorizedException
from src.schemas.responses.auth import Token
from src.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.role import RoleEnum


class AuthController:

    def __init__(self,session:AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)

    async def create_user(self, email:EmailStr,password:str) -> Token:
        async with self.session.begin(): 
            try:
                exist_user = await self.get_user_by_email(email)
                if exist_user is not None:
                    raise BadRequestException(message='User already exist')
                role =  await self.role_repo.get_role_by_name(RoleEnum.ADMIN)
                password_hash = PasswordHandler.hash(password)
                user = await self.user_repo.create_user({
                    'email':email,
                    'password':password_hash,
                    'role_id':role.id
                })
                return Token(
                    access_token=JWTHandler.encode_access_token(payload={"sub": user.id,"role":user.role.name}),
                    refresh_token=JWTHandler.encode_refresh_token(payload={"sub": user.id,"role":user.role.name}),
                )
            except Exception:
                raise

    async def login(self, email: str, password: str) -> Token:
        try:
            user = await self.get_user_by_email(email)
            if user is None:
                raise BadRequestException(message="User not found")
            if not PasswordHandler.verify(user.password,password):
                raise UnauthorizedException(message='Incorrect Password')
            return Token(
                    access_token=JWTHandler.encode_access_token(payload={"sub": user.id,"role":user.role.name}),
                    refresh_token=JWTHandler.encode_refresh_token(payload={"sub": user.id,"role":user.role.name}),
                )
        except Exception:
            raise
    
    async def get_user_by_email(self,email: str)-> User:
        try:
            user = await self.user_repo.get_by_email(email)
            return user
        except Exception:
            raise

    async def get_current_user(self,user_id: int)-> User:
        try:
            user = await self.user_repo.get_current_user(user_id)
            return user
        except Exception:
            raise 