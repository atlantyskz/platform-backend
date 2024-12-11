from typing import Any, List
from pydantic import EmailStr
from sqlalchemy import insert, select, update
from src.models.user import User
from src.models.organization import Organization
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

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