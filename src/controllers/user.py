

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from src.repositories.organization_member import OrganizationMemberRepository
from src.models.role import RoleEnum
from src.repositories.user import UserRepository
from src.repositories.role import RoleRepository
from src.controllers import BaseController
from src.models import User
from src.core.security import JWTHandler
from src.core.password import PasswordHandler
from src.core.exceptions import BadRequestException,UnauthorizedException
from src.schemas.responses.auth import Token
from src.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class UserController:

    def __init__(self,session:AsyncSession):
        self.session = session
        self.user_repo = UserRepository(self.session)
        self.role_repo = RoleRepository(self.session)
        self.organization_members_repo = OrganizationMemberRepository(self.session)

