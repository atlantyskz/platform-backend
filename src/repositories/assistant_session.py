from sqlalchemy import insert, select, update
from src.models.user import User
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.models.assistant_session import AssistantSession
from src.models.role import RoleEnum


class AssistantSessionRepository(BaseRepository):
    
    def __init__(self,session:AsyncSession):
        self.session = session

    async def create_session(self,attributes:dict)->AssistantSession:
        stmt = (insert(AssistantSession).values(**attributes).returning(AssistantSession))
        result = await self.session.execute(stmt)
        self.session.commit()
        return result.scalars().first()
    