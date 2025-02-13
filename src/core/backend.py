from typing import List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.favorite_resume import FavoriteResume
from src.models.hr_assistant_task import HRTask
from sqlalchemy import Integer, case, cast, func, insert,select
from src.core.databases import get_session
from sqlalchemy import desc, case, cast, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import joinedload
class BackgroundTasksBackend:

    def __init__ (self,session: AsyncSession):
        self.session = session

    

    async def create_task(self, attributes: dict) -> HRTask:
        # Создаем объект HRTask с аттрибутами
        task = HRTask(**attributes)
        
        # Добавляем объект в сессию
        self.session.add(task)
        
        # Делаем commit, чтобы сохранить объект в базе данных
        await self.session.flush()
        
        # Возвращаем сохраненный объект
        return task

    async def update_task_result(self, task_id: str, result_data: dict, tokens_spent: int, status: str = 'completed'):
        stmt = await self.session.execute(select(HRTask).where(HRTask.task_id == task_id))
        task = stmt.scalars().first()
        if task:
            task.result_data = result_data
            task.task_status = status
            task.tokens_spent = tokens_spent            
    async def get_results_by_session_id(self, session_id: str, user_id: int, offset: int = 0, limit: int = 10) -> List[HRTask]:
        favorite_subquery = (
            select(FavoriteResume.resume_id)
            .where(FavoriteResume.user_id == user_id)
            .subquery()
        )

        query = (
            select(
                HRTask,
                favorite_subquery.c.resume_id.isnot(None).label("is_favorite")
            )
            .outerjoin(
                favorite_subquery,
                HRTask.id == favorite_subquery.c.resume_id
            )
            .where(HRTask.session_id == session_id)
        )

        result = await self.session.execute(query)
        tasks = result.all()

        sorted_tasks = sorted(
            tasks,
            key=lambda task: (
                task[0].task_status == "completed",                 
            int(task[0].result_data.get("analysis", {}).get("matching_percentage", 0)) if task[0].result_data else 0            ),
            reverse=True
        )

        paginated_tasks = sorted_tasks[offset:offset + limit]

        return paginated_tasks
    

    async def get_results_by_session_id_ws(self,session_id:int)-> List[HRTask]:

        query = (
            select(HRTask,)
            .where(HRTask.session_id == session_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_session_results_to_export(self,session_id:str)-> List[HRTask]:
        stmt = select(HRTask).where(HRTask.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()    
    

    async def get_by_task_id(self,task_id:str):
        stmt = select(HRTask).where(HRTask.task_id == task_id).options(
            joinedload(HRTask.session)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()    

