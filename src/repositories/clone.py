# src/repositories/clone_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert
from src.models.clone import Clone
from typing import Optional

class CloneRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_clone(self, attributes: dict) -> Clone:
        clone  = Clone(**attributes)
        self.session.add(clone)
        await self.session.flush()
        return clone

    async def get_clone_by_id(self, clone_id: int) -> Optional[Clone]:
        stmt = select(Clone).where(Clone.id == clone_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self,):
        stmt = select(Clone)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_status(self, clone_id: int, status: str) -> Optional[Clone]:
        clone = await self.get_clone_by_id(clone_id)
        if clone:
            clone.status = status
            await self.session.commit()
            return clone
        return None
