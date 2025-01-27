

from datetime import timedelta
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from src.services.email import EmailService
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
        self.email_service = EmailService()

    async def create_user(self, email: EmailStr, password: str) -> dict:
        async with self.session.begin():
            try:
                # Проверяем существующего пользователя
                user = await self.user_repo.get_by_email(email)
                if user is not None:
                    raise HTTPException(status_code=400, detail="User already exists")
                
                # Получаем роль и создаем пользователя
                role = await self.role_repo.get_role_by_name(RoleEnum.ADMIN)
                password_hash = PasswordHandler.hash(password)
                user = await self.user_repo.create_user({
                    'email': email,
                    'password': password_hash,
                    'role_id': role.id
                })

                # Генерируем токен для подтверждения email
                verification_token = JWTHandler.encode_email_token(
                    payload={"sub": email, "type": "verification"}
                )
                verification_link = f"{self.email_service.frontend_url}/verify-email?token={verification_token}"
                html_content = f"""
                <h2>Welcome to Our Platform!</h2>
                <p>Please verify your email address by clicking the link below:</p>
                <a href="{verification_link}">Verify Email</a>
                <p>This link will expire in 1 hour.</p>
                """

                # Отправляем email
                await self.email_service.send_email(
                    to_email=email,
                    subject="Verify Your Email",
                    html_content=html_content
                )

                # Возвращаем ответ
                return {"message": "Verification has been sent to your email, please check it out"}
            except Exception as e:
                raise e            

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

    async def refresh_token(self,refresh_token: str)->Token:
        try:
            user_payload = JWTHandler.decode(refresh_token)
            if user_payload.get('type') != 'refresh':
                raise BadRequestException('Invalid refresh token')
            user_id = user_payload.get('sub')
            user = await self.user_repo.get_by_user_id(user_id)
            if user is None:
                raise UnauthorizedException(message="User not found")
            return Token(
                access_token=JWTHandler.encode_access_token(payload={"sub": user.id,"role":user.role.name}),
                refresh_token=JWTHandler.encode_refresh_token(payload={"sub": user.id,"role":user.role.name}),
                )
        except Exception:
            raise

        

    async def request_to_reset_password(self, email: str):
        try:
            user = await self._get_user_by_email(email)
            reset_token = JWTHandler.encode_email_token(
                payload={"sub": user.id, "type": "password_reset"},
            )

            reset_link = f"{self.email_service.frontend_url}/reset-password?token={reset_token}"
            html_content = f"""
            <h2>Password Reset Request</h2>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_link}">Reset Password</a>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
            """

            await self.email_service.send_email(
                to_email=email,
                subject="Password Reset Request",
                html_content=html_content
            )
            
            return {"message": "Password reset instructions sent to your email"}
        except Exception as e:
            raise BadRequestException(str(e))

    async def reset_password(self, token: str, new_password: str) -> dict:
        async with self.session.begin():
            try:
                payload = JWTHandler.decode(token)
                if payload.get('type') != 'password_reset':
                    raise BadRequestException('Invalid password reset token')
                
                user_id = payload.get('sub')
                user = await self.user_repo.get_by_user_id(user_id)
                
                if user is None:
                    raise BadRequestException('User not found')
                
                password_hash = PasswordHandler.hash(new_password)
                await self.user_repo.update_user(user.id, {'password': password_hash})
                
                # Send confirmation email
                html_content = """
                <h2>Password Reset Successful</h2>
                <p>Your password has been successfully reset.</p>
                <p>If you didn't make this change, please contact support immediately.</p>
                """
                
                await self.email_service.send_email(
                    to_email=user.email,
                    subject="Password Reset Successful",
                    html_content=html_content
                )
                
                return {"message": "Password reset successfully"}
            except BadRequestException as e:
                raise e
            except Exception as e:
                raise BadRequestException(str(e))
        
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

    async def verify_email(self, token: str) -> dict:
        try:
            async with self.session.begin():
                payload = JWTHandler.decode(token)
                print(payload)
                if payload.get('type') != 'verification':
                    raise BadRequestException('Invalid verification token')
                
                email = payload.get('sub')
                user = await self.user_repo.get_by_email(email)
                
                if user is None:
                    raise BadRequestException('User not found')
                if user.is_verified:
                    raise BadRequestException('Email already verified')
                
                await self.user_repo.update_user(user.id, {'is_verified': True})
                return Token(
                        access_token=JWTHandler.encode_access_token(payload={"sub": user.id,"role":user.role.name}),
                        refresh_token=JWTHandler.encode_refresh_token(payload={"sub": user.id,"role":user.role.name}),
                    )
        except Exception as e:
            await self.session.rollback()
            raise BadRequestException(str(e))