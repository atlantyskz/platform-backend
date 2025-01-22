from sqlalchemy import delete, insert, select, update
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.chat_message_history import ChatMessageHistory


class ChatHistoryMessageRepository(BaseRepository):
    
    def __init__(self,session:AsyncSession):
        self.session = session

    async def create(self,attributes: dict):
        history = ChatMessageHistory(**attributes)
        self.session.add(history)
        await self.session.flush()
        return history
    
    async def get_all_by_session_id(self,session_id:str)->ChatMessageHistory:
        res = await self.session.execute(
            select(ChatMessageHistory).where(ChatMessageHistory.session_id == session_id).order_by(ChatMessageHistory.created_at)
        )
        return res.scalars().all()
    
    
    async def update_by_session_id(self,session_id:str,attributes: dict)->ChatMessageHistory:
        res = await self.session.execute(
            update(ChatMessageHistory).values(**attributes).returning(ChatMessageHistory)
        )
        await self.session.flush()
        return res.scalars().first()
