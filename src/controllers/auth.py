

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
                user =await self.user_repo.get_by_email(email)
                if user is not None:
                    raise BadRequestException("User already Exist")
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
            user = await self._get_user_by_email(email)
            if not PasswordHandler.verify(user.password,password):
                raise UnauthorizedException(message='Incorrect Password')
            return Token(
                    access_token=JWTHandler.encode_access_token(payload={"sub": user.id,"role":user.role.name}),
                    refresh_token=JWTHandler.encode_refresh_token(payload={"sub": user.id,"role":user.role.name}),
                )
        except Exception:
            raise

    async def request_to_reset_password(self, email:str ):
        try:
            user = await self._get_user_by_email(email)
            token = JWTHandler.encode_access_token
            
        except Exception as e:
            raise   

    async def reset_password(self,email: str)->str:
        try:
            user = await self._get_user_by_email(email)
            
        except Exception as e:
            raise   

    async def _get_user_by_email(self,email: str)-> User:
        try:
            user = await self.user_repo.get_by_email(email)
            if user is None:
                raise BadRequestException(message='User not found')
            return user
        except Exception:
            raise

    async def get_current_user(self,user_id: int)-> User:
        try:
            user = await self.user_repo.get_current_user(user_id)
            return user
        except Exception:
            raise 