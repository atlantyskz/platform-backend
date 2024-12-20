from typing import List
from sqlalchemy import insert, select
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.assistant_session import AssistantSession
from src.models.assistant import Assistant


class AssistantSessionRepository(BaseRepository):
    
    def __init__(self,session:AsyncSession):
        self.session = session

    async def create_session(self,attributes:dict)->AssistantSession:
        stmt = (insert(AssistantSession).values(**attributes).returning(AssistantSession))
        result = await self.session.execute(stmt)
        self.session.commit()
        return result.scalars().first()
    
    async def get_by_user_id(self,user_id:int)-> List[AssistantSession]:
        stmt = (
                select(AssistantSession, Assistant.name) 
                .join(Assistant, Assistant.id == AssistantSession.assistant_id)
                .where(AssistantSession.user_id == user_id)
            )
        result = await self.session.execute(stmt)        
        sessions_with_names = [
            {   
                'session_id': session.id,
                'title':session.title,
                'assistant_id': session.assistant_id,
                'assistant_name': assistant_name
            }
            for session, assistant_name in result.fetchall()
        ]
        return sessions_with_names