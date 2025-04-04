import os
from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BadRequestException, UnauthorizedException, NotFoundException
from src.core.password import PasswordHandler
from src.core.security import JWTHandler
from src.core.tasks import free_trial_tracker
from src.models import User
from src.models.role import RoleEnum
from src.repositories.balance import BalanceRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.organization_member import OrganizationMemberRepository
from src.repositories.role import RoleRepository
from src.repositories.user import UserRepository
from src.repositories.user_cache_balance import UserCacheBalanceRepository
from src.schemas.responses.auth import Token
from src.services.email import EmailService

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "https://platform.atlantys.kz/google-auth"

CLIENT_SECRETS_FILE = "client_secret.json"


class AuthController:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)
        self.organization_repo = OrganizationRepository(session)
        self.balance_repo = BalanceRepository(session)
        self.organization_member_repo = OrganizationMemberRepository(session)
        self.email_service = EmailService()
        self.user_cache_balance_repo = UserCacheBalanceRepository(session)

    async def create_user(self, email: EmailStr, phone_number: str, password: str) -> Token:
        async with self.session.begin():
            try:
                # Проверяем существующего пользователя
                user = await self.user_repo.get_by_email(email)
                if user is not None:
                    raise HTTPException(status_code=400, detail="User with this email already exists")
                user = await self.user_repo.get_by_phone_number(phone_number)
                if user is not None:
                    raise HTTPException(status_code=400, detail="User with this phone number already exists")

                # Получаем роль и создаем пользователя
                role = await self.role_repo.get_role_by_name(RoleEnum.ADMIN)
                password_hash = PasswordHandler.hash(password)
                user = await self.user_repo.create_user({
                    'email': email,
                    'phone_number': phone_number,
                    'password': password_hash,
                    'role_id': role.id
                })
                organization = await self.organization_repo.add({'name': 'Company name', 'email': email})
                await self.session.flush()
                await self.organization_member_repo.add(
                    organization.id,
                    'admin',
                    user.id,
                )
                await self.session.flush()

                balance = await self.balance_repo.create_balance({
                    'organization_id': organization.id,
                    'atl_tokens': 15,
                    'free_trial': True
                })
                await self.user_cache_balance_repo.create_cache_balance(
                    {
                        "user_id": user.id,
                        "balance": 0,
                    }
                )
                await self.session.flush()
                # call cron job ...
                free_trial_tracker.apply_async(kwargs={"balance_id": balance.id},
                                               eta=balance.created_at + timedelta(days=1))
                return Token(
                    access_token=JWTHandler.encode_access_token(payload={"sub": user.id, "role": user.role.name}),
                    refresh_token=JWTHandler.encode_refresh_token(payload={"sub": user.id, "role": user.role.name}),
                )
            except Exception as e:
                raise e

    async def login(self, password: str, email: str | None = None, phone_number: str | None = None) -> Token:
        try:
            if email:
                user = await self._get_user_by_email(email)
                if not user:
                    raise NotFoundException("User with this email does not exist")

            elif phone_number:
                user = await self.user_repo.get_by_phone_number(phone_number)
                if not user:
                    raise NotFoundException("User with this phone number does not exist")
            else:
                raise BadRequestException("Either email or phone_number must be provided")

            if not PasswordHandler.verify(user.password, password):
                raise UnauthorizedException(message='Incorrect Password')
            return Token(
                access_token=JWTHandler.encode_access_token(payload={"sub": user.id, "role": user.role.name}),
                refresh_token=JWTHandler.encode_refresh_token(payload={"sub": user.id, "role": user.role.name}),
            )
        except Exception:
            raise

    async def refresh_token(self, refresh_token: str) -> Token:
        try:
            user_payload = JWTHandler.decode(refresh_token)
            if user_payload.get('type') != 'refresh':
                raise BadRequestException('Invalid refresh token')
            user_id = user_payload.get('sub')
            user = await self.user_repo.get_by_user_id(user_id)
            if user is None:
                raise UnauthorizedException(message="User not found")
            return Token(
                access_token=JWTHandler.encode_access_token(payload={"sub": user.id, "role": user.role.name}),
                refresh_token=JWTHandler.encode_refresh_token(payload={"sub": user.id, "role": user.role.name}),
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

    async def _get_user_by_email(self, email: str) -> User:
        try:
            user = await self.user_repo.get_by_email(email)
            if user is None:
                raise BadRequestException(message='User not found')
            return user
        except Exception:
            raise

    async def get_current_user(self, user_id: int) -> User:
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
                    access_token=JWTHandler.encode_access_token(payload={"sub": user.id, "role": user.role.name}),
                    refresh_token=JWTHandler.encode_refresh_token(payload={"sub": user.id, "role": user.role.name}),
                )
        except Exception as e:
            await self.session.rollback()
            raise BadRequestException(str(e))

    async def google_auth(self, request: Request):
        """
        Инициализирует OAuth2 поток и перенаправляет пользователя на страницу авторизации Google.
        """
        # Используем полные URL для скоупов
        scopes = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email"
        ]
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=scopes,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent"
        )
        # Рекомендуется сохранить state для проверки в callback (например, в сессии)
        return RedirectResponse(url=authorization_url)

    async def google_auth_callback(self, params: dict):
        query_params = params
        if "error" in query_params:
            raise HTTPException(status_code=400, detail=f"Auth error: {query_params['error']}")
        code = query_params.get("code")
        state = query_params.get("state")
        if not code:
            raise HTTPException(status_code=400, detail="Auth code is not valid")

        scopes = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email"
        ]
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=scopes,
            redirect_uri=GOOGLE_REDIRECT_URI,
            state=state
        )
        try:
            flow.fetch_token(code=code)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Auth code is not valid: {str(e)}")

        credentials = flow.credentials

        try:
            oauth2_client = build("oauth2", "v2", credentials=credentials)
            user_info = oauth2_client.userinfo().get().execute()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error during receiving user info : {str(e)}")

        if not user_info.get("email"):
            raise HTTPException(status_code=400, detail="Email not found")
        async with self.session.begin():
            user = await self.user_repo.get_by_email(user_info.get("email"))
            if user is None:
                role = await self.role_repo.get_role_by_name(RoleEnum.ADMIN)
                password_hash = PasswordHandler.hash(str(uuid4()))
                user = await self.user_repo.create_user({
                    'email': user_info.get("email"),
                    'password': password_hash,
                    'role_id': role.id
                })
                organization = await self.organization_repo.add(
                    {'name': 'Top Company', 'email': user_info.get("email")})
                await self.session.flush()
                await self.organization_member_repo.add(
                    organization.id,
                    'admin',
                    user.id,
                )
                await self.session.flush()

                await self.balance_repo.create_balance({
                    'organization_id': organization.id,
                    'atl_tokens': 100,
                    'free_trial': True
                })
            user_role = user.role if user.role is not None else await self.role_repo.get_role_by_name(RoleEnum.ADMIN)
            access_token = JWTHandler.encode_access_token(payload={"sub": user.id, "role": user_role.name})
            refresh_token = JWTHandler.encode_refresh_token(payload={"sub": user.id, "role": user_role.name})
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
