from sqlalchemy import select,update,delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.vacancy import Vacancy
from src.repositories import BaseRepository

class VacancyRepository(BaseRepository):

    def __init__(self,session:AsyncSession):
        self.session = session

    async def add(self,attributes:dict):
        vacancy = Vacancy(**attributes)
        self.session.add(vacancy)
        await self.session.commit()
        await self.session.refresh(vacancy)
        return vacancy
    
    async def get_by_id(self, id:str)->Vacancy:
        stmt = select(Vacancy).where(Vacancy.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_by_user_id(self,user_id:int)->Vacancy:
        stmt = select(Vacancy).where(Vacancy.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    
    async def update_by_id(self,id:str,attributes:dict):
        stmt = (
            update(Vacancy)
            .where(Vacancy.id == id)
            .values(vacancy_text=attributes)
            .execution_options(synchronize_session="fetch")
            .returning(Vacancy)
        )        
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete_vacancy(self,id:str):
        stmt = (
            delete(Vacancy).where(Vacancy.id==id)
        )
        await self.session.execute(stmt)
        await self.session.commit()

