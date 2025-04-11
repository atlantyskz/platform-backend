from typing import List

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import InterviewIndividualQuestion
from src.repositories import BaseRepository


class InterviewIndividualQuestionRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_question(self, data: dict) -> InterviewIndividualQuestion:
        stmt = insert(InterviewIndividualQuestion).values(**data).returning(InterviewIndividualQuestion.id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_question_by_id(self, question_id: int) -> InterviewIndividualQuestion:
        stmt = select(InterviewIndividualQuestion).where(InterviewIndividualQuestion.id == question_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_question(self, question_id: int, data: dict) -> InterviewIndividualQuestion:
        stmt = (
            update(InterviewIndividualQuestion)
            .where(InterviewIndividualQuestion.id == question_id)
            .values(**data)
            .returning(InterviewIndividualQuestion)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete_question(self, question_id: int) -> int:
        stmt = delete(InterviewIndividualQuestion).where(InterviewIndividualQuestion.id == question_id)
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_questions_by_resume(self, resume_id: int) -> List[InterviewIndividualQuestion]:
        stmt = (
            select(
                InterviewIndividualQuestion
            )
            .where(
                InterviewIndividualQuestion.resume_id == resume_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
