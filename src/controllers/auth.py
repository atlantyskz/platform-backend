

from datetime import timedelta
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from src.repositories.organization_member import OrganizationMemberRepository
from src.repositories.balance import BalanceRepository
from src.services.email import EmailService
from src.repositories.role import RoleRepository
from src.repositories.user import UserRepository
from src.repositories.organization import OrganizationRepository
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
        self.organization_repo = OrganizationRepository(session)   
        self.balance_repo = BalanceRepository(session)
        self.organization_member_repo = OrganizationMemberRepository(session)
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
                organization = await self.organization_repo.get_organization(1)
                await self.organization_member_repo.add(
                    organization.id,
                    'admin',
                    user.id,
                )
                # await self.balance_repo.create_balance({'organization_id':organization.id,'atl_tokens':10})
                
                # verification_token = JWTHandler.encode_email_token(
                #     payload={"sub": email, "type": "verification"}
                # )
                # verification_link = f"{self.email_service.frontend_url}/verify-email?token={verification_token}"
                # html_content = f"""
                # <h2>Добро пожаловать на нашу платформу!</h2>
                # <p>Пожалуйста, подтвердите свой адрес электронной почты, кликнув по ссылке ниже:</p>
                # <a href="{verification_link}">Подтвердить email</a>
                # <p>Ссылка будет действительна в течение 1 часа.</p>

                # """

                # await self.email_service.send_email(
                #     to_email=email,
                #     subject="Verify Your Email",
                #     html_content=html_content
                # )

                return Token(
                    access_token=JWTHandler.encode_access_token(payload={"sub": user.id,"role":user.role.name}),
                    refresh_token=JWTHandler.encode_refresh_token(payload={"sub": user.id,"role":user.role.name}),
                ).model_dump_json()
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
            <h2>Запрос на сброс пароля</h2>
            <p>Нажмите на ссылку ниже, чтобы сбросить пароль:</p>
            <a href="{reset_link}">Сбросить пароль</a>
            <p>Ссылка будет действительна в течение 1 часа.</p>
            <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
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
                <h2>Сброс пароля успешно выполнен</h2>
                <p>Ваш пароль был успешно сброшен.</p>
                <p>Если вы не совершали это действие, пожалуйста, немедленно свяжитесь со службой поддержки.</p>

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