from typing import Callable, List

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.interview_common_question import InterviewCommonQuestion
from src.repositories import BaseRepository


class InterviewCommonQuestionRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_question(self, data: dict) -> InterviewCommonQuestion:
        stmt = (insert(InterviewCommonQuestion).values(**data).returning(InterviewCommonQuestion.id))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_question_by_id(self, question_id: int) -> InterviewCommonQuestion:
        stmt = (select(InterviewCommonQuestion).where(InterviewCommonQuestion.id == question_id))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_question(self, question_id: int, data: dict) -> InterviewCommonQuestion:
        stmt = (
            update(InterviewCommonQuestion).where(InterviewCommonQuestion.id == question_id).values(**data).returning(
                InterviewCommonQuestion))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete_question(self, question_id: int) -> Callable[[], int]:
        stmt = delete(InterviewCommonQuestion).where(InterviewCommonQuestion.id == question_id)
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_session_questions(self, session_id: str) -> List[InterviewCommonQuestion]:
        stmt = (select(InterviewCommonQuestion).where(InterviewCommonQuestion.session_id == session_id))
        result = await self.session.execute(stmt)
        return result.scalars().all()
