from typing import List, Optional
from sqlalchemy import delete, insert, select, update
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.assistant_session import AssistantSession
from src.models.assistant import Assistant


class AssistantSessionRepository(BaseRepository):
    
    def __init__(self,session:AsyncSession):
        self.session = session

    async def create_session(self,attributes:dict)->AssistantSession:
        assistant_session = AssistantSession(**attributes)
        self.session.add(assistant_session)
        await self.session.flush()
        return assistant_session    
    
    async def update_session(self,session_id:str,attributes:dict):
        stmt = (
            update(AssistantSession)
            .where(AssistantSession.id == session_id)
            .values(**attributes)
            .execution_options(synchronize_session="fetch")
            .returning(AssistantSession)
        )        
        result = await self.session.execute(stmt)
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
    
    async def get_by_session_id(self, session_id: str) -> Optional[AssistantSession]:
        stmt = (
            select(AssistantSession)
            .where(AssistantSession.id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()     
    
    async def delete_session(self,session_id:str):
        
        stmt = (
            delete(AssistantSession).where(AssistantSession.id == session_id)
        )
        await self.session.execute(stmt)
        await self.session.commit()