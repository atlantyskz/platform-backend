from typing import Optional

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.favorite_resume import FavoriteResume
from src.models.hr_assistant_task import HRTask
from src.repositories import BaseRepository


class FavoriteResumeRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, attributes: dict) -> FavoriteResume:
        favorite_resume = FavoriteResume(**attributes)
        self.session.add(favorite_resume)
        return favorite_resume

    async def delete_by_resume_id(self, user_id: int, resume_id: int):
        print(resume_id)
        stmt = select(FavoriteResume).where(FavoriteResume.resume_id == resume_id, FavoriteResume.user_id == user_id)
        result = await self.session.execute(stmt)
        resume = result.scalars().first()
        return resume

    async def get_favorite_resumes_by_user_id(self, user_id: int, session_id: str) -> FavoriteResume:
        stmt = select(HRTask).join(FavoriteResume, HRTask.id == FavoriteResume.resume_id).where(
            FavoriteResume.user_id == user_id, HRTask.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_favorite_resume_by_user_id(self, user_id: int, resume_id: int, session_id: str) -> FavoriteResume | None:
        stmt = select(HRTask).join(FavoriteResume, HRTask.id == FavoriteResume.resume_id).where(
            FavoriteResume.user_id == user_id, FavoriteResume.resume_id == resume_id, HRTask.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_favorite_resumes_by_resume_id(self, resume_id: int) -> FavoriteResume | None:
        stmt = select(FavoriteResume).where(FavoriteResume.resume_id == resume_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_resume(self, resume_id):
        stmt = select(HRTask).where(HRTask.id == resume_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_result_data_by_resume_id(self, resume_id: int) -> Optional[dict]:
        query = (
            select(HRTask.result_data)
            .join(FavoriteResume, HRTask.id == FavoriteResume.resume_id)
            .where(FavoriteResume.resume_id == resume_id)
        )
        result = await self.session.execute(query)
        hr_task = result.scalar()
        return hr_task

    async def update_questions_for_candidate(self, resume_id: int, questions: dict):
        query = (
            select(FavoriteResume)
            .where(FavoriteResume.resume_id == resume_id)
        )
        result = await self.session.execute(query)
        favorite_resume = result.scalar()
        if favorite_resume:
            favorite_resume.question_for_candidate = questions
            await self.session.commit()
        return favorite_resume

    async def update_favorite_resume(self, resume_id: int | None, call_sid: str | None, upd_data: dict):
        query = (
            update(FavoriteResume)
            .where(
                or_(
                    FavoriteResume.id == resume_id if resume_id is not None else False,
                    FavoriteResume.call_sid == call_sid if call_sid is not None else False
                )
            )
            .values(**upd_data)
        )
        await self.session.execute(query)
        await self.session.commit()

    async def get_result_data_by_resume_id(self, resume_id: int) -> Optional[dict]:
        query = (
            select(HRTask.result_data)
            .join(FavoriteResume, HRTask.id == FavoriteResume.resume_id)
            .where(FavoriteResume.resume_id == resume_id)
        )
        result = await self.session.execute(query)
        hr_task = result.scalar()
        return hr_task
