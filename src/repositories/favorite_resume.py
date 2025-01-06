from sqlalchemy import select, delete
from src.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.favorite_resume import FavoriteResume
from src.models.hr_assistant_task import HRTask


class FavoriteResumeRepository(BaseRepository):
    
    def __init__(self,session:AsyncSession):
        self.session = session

    async def add(self,attributes:dict)->FavoriteResume:
        favorite_resume = FavoriteResume(**attributes)
        self.session.add(favorite_resume)
        return favorite_resume
    

    async def delete_by_resume_id(self, user_id: int,resume_id:int):
        print(resume_id)
        stmt = select(FavoriteResume).where(FavoriteResume.resume_id == resume_id,FavoriteResume.user_id == user_id)

        result = await self.session.execute(stmt)

        resume = result.scalars().first()  
        return resume        

    async def get_favorite_resumes_by_user_id(self,user_id:int,session_id:str)->FavoriteResume:
        stmt = select(HRTask).join(FavoriteResume,HRTask.id == FavoriteResume.resume_id).where(FavoriteResume.user_id == user_id,HRTask.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_favorite_resumes_by_resume_id(self,resume_id:int)->FavoriteResume|None:
        stmt = select(FavoriteResume).where(FavoriteResume.resume_id == resume_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_resume(self,resume_id):
        stmt = select(HRTask).where(HRTask.id == resume_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    
