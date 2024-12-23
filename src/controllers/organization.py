

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from src.repositories.organization_member import OrganizationMemberRepository
from src.repositories.user import UserRepository
from src.controllers import BaseController
from src.models import Organization
from src.models.role import RoleEnum
from src.core.security import JWTHandler
from src.core.password import PasswordHandler
from src.core.exceptions import BadRequestException,UnauthorizedException
from src.schemas.responses.auth import Token
from src.repositories.user import UserRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.role import RoleRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

class OrganizationController:

    def __init__(self,session:AsyncSession):
        self.session = session
        self.user_repo = UserRepository(self.session)
        self.organization_repo = OrganizationRepository(self.session)
        self.organization_members_repo = OrganizationMemberRepository(self.session)
        self.role_repository = RoleRepository(self.session)

    async def get_organization_info(self, user_id: int):
        try:
            user_organization = await self.organization_repo.get_user_organization(user_id)
            if user_organization is None:
                raise BadRequestException(message="User is not a member of any organization.")

            organization_assistants = await self.organization_repo.get_assistants_by_organization(user_organization.id)
            
            # Получаем всех членов организации
            members = await self.organization_members_repo.get_organization_employees(user_organization.id)
            return {
                "organization": {
                    "id": user_organization.id,
                    "name": user_organization.name,
                    "email": user_organization.email,
                    "phone_number": user_organization.phone_number,
                    "registered_address": user_organization.registered_address,
                },
                "members": members,
                "organization_assistants": [
                    {
                        "id": assistant.id,
                        "name": assistant.name,
                        "description": assistant.description,
                        "status": assistant.status,
                        "type": assistant.type,
                    }
                    for assistant in organization_assistants.assistants  
                ]
            }
        except Exception as e:
            raise
        

    async def create_organization(self, name:str,email:str,phone_number:str,registered_address:str,admin_id:int) -> Organization:
        try:
            async with self.session.begin():
                user = await self.user_repo.get_by_user_id(admin_id)
                if user is None:
                    raise BadRequestException(message='Invalid Request')
                existing_organization = await self.organization_members_repo.get_organization_by_user_role(admin_id,RoleEnum.ADMIN)
                if existing_organization is not None:
                    raise BadRequestException(message='You already created organization')
                new_org = await self.organization_repo.add({
                    "name":name,
                    "email":email,
                    "phone_number":phone_number,
                    "registered_address":registered_address,
                })
                await self.session.flush()
                await self.session.refresh(new_org)

                new_org_member = await self.organization_members_repo.add(
                    organization_id=new_org.id,
                    employee_id=user.id,
                    role_alias=user.role.name
                )
                await self.session.flush()
                org_name = new_org.name
            return {"success":True}
        except SQLAlchemyError as e:
            raise
        except Exception as e:
            raise


    async def update_organization(self,attributes:dict,admin_id:int) -> Organization:
        try:
            organization = await self.organization_members_repo.get_organization_by_user_role(admin_id,RoleEnum.ADMIN)
            if organization is None:
                raise BadRequestException(message='Not Found')
            updated_organization = await self.organization_repo.update(organization.organization_id,attributes)
            return updated_organization
        except Exception:
            raise
            
            
