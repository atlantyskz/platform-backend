from typing import List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
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

    async def update_task_result(self,task_id:str,result_data:dict,status:str = 'completed'):
        stmt = await self.session.execute(select(HRTask).where(HRTask.task_id == task_id))
        task = stmt.scalars().first()
        if task:
            task.result_data = result_data
            task.task_status = status
            await self.session.commit()
        


    async def get_results_by_session_id(self,session_id: int, offset:int = 0, limit:int = 10)->List[HRTask]:
        result = await self.session.execute(
            select(HRTask)
            .where(HRTask.session_id == session_id)
            .offset(offset)
            .limit(limit)    
        )
        return result.scalars().all()
