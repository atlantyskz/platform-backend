from typing import List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.favorite_resume import FavoriteResume
from src.models.hr_assistant_task import HRTask
from sqlalchemy import insert,select
from src.core.databases import get_session


class BackgroundTasksBackend:

    def __init__ (self,session: AsyncSession):
        self.session = session

    
    async def create_task(self,attributes:dict)->HRTask:
        stmt = (insert(HRTask).values(**attributes).returning(HRTask))
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()

    async def update_task_result(self,task_id:str,result_data:dict,tokens_spent:int,status:str = 'completed'):
        stmt = await self.session.execute(select(HRTask).where(HRTask.task_id == task_id))
        task = stmt.scalars().first()
        if task:
            task.result_data = result_data
            task.task_status = status
            task.tokens_spent = tokens_spent
            await self.session.commit()
        
    async def get_results_by_session_id(self, session_id: str, user_id: int, offset: int = 0, limit: int = 10) -> List[HRTask]:
        # Подзапрос для избранного
        favorite_subquery = (
            select(FavoriteResume.resume_id)
            .where(FavoriteResume.user_id == user_id)
            .subquery()
        )

        # Основной запрос с LEFT JOIN
        query = (
            select(HRTask, favorite_subquery.c.resume_id.isnot(None).label("is_favorite"))
            .outerjoin(
                favorite_subquery,  
                HRTask.id == favorite_subquery.c.resume_id  
            )
            .where(HRTask.session_id == session_id)
        )

        # Пагинация
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        # Выполнение запроса
        result = await self.session.execute(query)
        return result.all()