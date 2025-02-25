from typing import  List
from sqlalchemy import insert, select, update
from src.models.organization_member import OrganizationMember
from src.models.organization import Organization
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import subqueryload,selectinload


class OrganizationRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, attributes: dict) -> Organization:
        stmt = insert(Organization).values(**attributes).returning(Organization)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def add(self,attributes: dict) -> Organization:
        new_org = Organization(**attributes)
        self.session.add(new_org)
        return new_org
    
    async def get_organization(self,id: int) -> Organization:
        stmt = select(Organization).where(Organization.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all_organizations(self,)->List[Organization]:
        stmt = select(Organization)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_organization(self, user_id: int) -> Organization | None:
        stmt = (
            select(Organization)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(OrganizationMember.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self,organization_id,attributes:dict)-> Organization:
        stmt = (
            update(Organization)
            .where(Organization.id == organization_id)
            .values(**attributes)
            .returning(Organization)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()
    

    async def get_assistants_by_organization(self, organization_id: int):
        stmt = select(Organization).options(
            selectinload(Organization.assistants)  
        ).where(Organization.id == organization_id)

        result = await self.session.execute(stmt)
        organization = result.scalar_one_or_none()  #
        return organization

    async def get_organization_by_name(self, name:str):
        stmt = select(Organization).where(Organization.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()
