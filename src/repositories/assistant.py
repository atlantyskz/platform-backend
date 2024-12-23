from sqlalchemy import delete, insert, select
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.assistant import Assistant
from src.models.assigned_assistant import assigned_assistant


class AssistantRepository(BaseRepository):
    
    def __init__(self,session:AsyncSession):
        self.session = session

    async def create_assistant(self,attributes: dict)-> Assistant:
        stmt = (insert(Assistant).values(**attributes).returning(Assistant))
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_assistant_by_id(self,id: int)-> Assistant:
        stmt = (select(Assistant).where(Assistant.id == id))
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def add_assistant_to_organization(self,organization_id:int,assistant_id:int)->assigned_assistant: # type: ignore
        stmt = (insert(assigned_assistant).values({
            'organization_id':organization_id,
            'assistant_id':assistant_id
        })).returning(assigned_assistant)
        result = await self.session.execute(stmt)
        return result.scalars().first()
        
    async def get_org_assistant(self, organization_id:int, assistant_id:int):
        stmt = select(assigned_assistant).where(
            (assigned_assistant.c.organization_id == organization_id) &
            (assigned_assistant.c.assistant_id == assistant_id)
        )
        result = await self.session.execute(stmt)        
        return result.scalars().first()
    
    async def delete_assigned_assistant(self, organization_id: int, assistant_id: int) -> None:
        stmt = delete(assigned_assistant).where(
            assigned_assistant.c.organization_id == organization_id,
            assigned_assistant.c.assistant_id == assistant_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount        
        