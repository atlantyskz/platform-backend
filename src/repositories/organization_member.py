from sqlalchemy import select, update
from src.models.user import User
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.models.organization_member import OrganizationMember
from src.models.role import RoleEnum


class OrganizationMemberRepository(BaseRepository):
    
    def __init__(self,session:AsyncSession):
        self.session = session


    async def add(self, organization_id: int, role_alias: str, employee_id: int) -> OrganizationMember:
        new_member = OrganizationMember(
            organization_id=organization_id,
            role_alias=role_alias,
            user_id=employee_id
        )
        self.session.add(new_member)
        return new_member

    async def get_all(self,organization_id:int,role_id:int)->OrganizationMember:
        stmt = (select(OrganizationMember)
                .where(OrganizationMember.organization_id == organization_id)
                .join(User)
                .where(User.role_id == role_id)
                .options(
                    joinedload(OrganizationMember.user)
                    .defer(User.password),
                    
                ))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_organization_by_user_role(self,user_id:int,role_alias:RoleEnum)->OrganizationMember:
        stmt = select(OrganizationMember).where(OrganizationMember.user_id == user_id,OrganizationMember.role_alias == role_alias.value)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
        
    async def update_org_member(self,user_id,attributes:dict)-> OrganizationMember:
        stmt = (
            update(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
            .values(**attributes)
            .returning(OrganizationMember)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_organization_employees(self, organization_id: int):
        stmt = (
            select(OrganizationMember)
            .options(
                joinedload(OrganizationMember.user).joinedload(User.role)
            )
            .where(
                OrganizationMember.organization_id == organization_id,
            )
        )
        result = await self.session.execute(stmt)
        members = result.scalars().all()

        return [
            {
                "id": member.user.id,
                "firstname": member.user.firstname,
                "lastname": member.user.lastname,
                "email": member.user.email,
                'role_alias':member.role_alias,
                "role_name": member.user.role.name if member.user.role else None, 
            }
            for member in members
        ]