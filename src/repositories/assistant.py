from sqlalchemy import insert, select, update
from src.models.user import User
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.models.assistant import Assistant
from src.models.role import RoleEnum


class AssistantRepository(BaseRepository):
    
    def __init__(self,session:AsyncSession):
        self.session = session

    async def create_assistant(self,attributes:dict)->Assistant:
        stmt = (insert(Assistant).values(**attributes).returning(Assistant))
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_assistant_by_id(self,id:int)->Assistant:
        stmt = (select(Assistant).where(Assistant.id == id))
        result = await self.session.execute(stmt)
        return result.scalars().first()