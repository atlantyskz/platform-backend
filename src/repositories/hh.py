from sqlalchemy import delete, insert, select, update
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.hh import HHAccount
from src.models.user import User

class HHAccountRepository(BaseRepository):
    
    def __init__(self,session:AsyncSession):
        self.session = session

    async def create_hh_account(self,attributes: dict)-> HHAccount:
        stmt = (insert(HHAccount).values(**attributes).returning(HHAccount))
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_hh_account_by_user_id(self,user_id: int)-> HHAccount:
        stmt = (select(HHAccount).where(HHAccount.user_id == user_id))
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def update_hh_account(self,user_id:int,attributes:dict)-> HHAccount:
        stmt = (update(HHAccount).where(HHAccount.user_id == user_id).values(**attributes).returning(HHAccount))
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def delete_hh_account(self,user_id:int)-> None:
        stmt = delete(HHAccount).where(HHAccount.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.rowcount
    