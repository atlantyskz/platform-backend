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
from src.core.exceptions import BadRequestException,UnauthorizedException,DuplicateValueException,NotFoundException
from src.schemas.responses.auth import Token
from src.repositories.user import UserRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.role import RoleRepository
from sqlalchemy.ext.asyncio import AsyncSession



class OrganizationMemberController:

    def __init__(self,session:AsyncSession):
        self.session = session
        self.user_repo = UserRepository(self.session)
        self.organization_repo = OrganizationRepository(self.session)
        self.organization_members_repo = OrganizationMemberRepository(self.session)
        self.role_repository = RoleRepository(self.session)

    async def create_organization_member(self, attributes:dict, admin_id:int) -> Organization:
        try:
            async with self.session.begin():
                user_admin = await self.user_repo.get_by_user_id(admin_id)
                if user_admin is None:
                    raise BadRequestException(message='Invalid Request')
                user_admin_organization = await self.organization_members_repo.get_organization_by_user_role(admin_id,RoleEnum.ADMIN)
                if user_admin_organization is None:
                    raise BadRequestException(message='You dont have organization')
                employee_role = await self.role_repository.get_role_by_name(RoleEnum.EMPLOYER)

                existing_user = await self.user_repo.get_by_email(attributes.get('email'))
                if existing_user is not None:   
                    raise DuplicateValueException(f"User with email {attributes.get('email')} already exists")
                hash_password = PasswordHandler.hash(attributes.get("password"))
                new_employee = await self.user_repo.create_user({
                    "email":attributes.get("email"),
                    "password":hash_password,
                    "firstname":attributes.get("firstname"),
                    "lastname":attributes.get("lastname"),
                    "role_id":employee_role.id
                })
                
                new_member = await self.organization_members_repo.add(
                    organization_id=user_admin_organization.organization_id,
                    role_alias=attributes.get('role_alias'),
                    employee_id=new_employee.id,
                )
                return new_member.__dict__
        except Exception as e:
            raise

    async def get_all_members_by_org_id(self,organization_id:int):
        try:
            organization = await self.organization_repo.get_organization(organization_id)
            employer_role = await self.role_repository.get_role_by_name(RoleEnum.EMPLOYER)
            if organization is None:
                raise NotFoundException(message="Organization not found")
            members = await self.organization_members_repo.get_all(organization_id,employer_role.id)
            return members if members else []
        except Exception:
            raise


    async def delete_member_from_organization(self,employee_id:int):
        try:
            async with self.session.begin():
                rowcount = await self.user_repo.delete_user(employee_id)
                return rowcount
        except Exception:
            raise


    async def update_organization(self,attributes: dict,admin_id:int) -> Organization:
        try:
            organization = await self.organization_members_repo.get_organization_by_user_role(admin_id,RoleEnum.ADMIN)
            if organization is None:
                raise BadRequestException(message='Not Found')
            updated_organization = await self.organization_repo.update(organization.organization_id,attributes)
            return updated_organization
        except Exception:
            raise
            

    async def update_user(self, attributes: dict, admin_id: int):
        try:
            user_id = attributes.pop('employee_id', admin_id)

            async with self.session.begin():
                role_alias = attributes.pop('role_alias', None)
                if role_alias:
                    await self.organization_members_repo.update_org_member(user_id, {"role_alias":role_alias})

                password = attributes.pop('password', None)
                if password:
                    attributes['password'] = PasswordHandler.hash(password)

                if attributes:
                    await self.user_repo.update_user(user_id, attributes)

            return {
                "success": True,
                "message": "Successfully updated"
            }

        except Exception as e:
            raise
