from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundException, BadRequestException
from src.repositories.favorite_resume import FavoriteResumeRepository
from src.repositories.interview_individual_question import InterviewIndividualQuestionRepository


class InterviewIndividualQuestionController:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.interview_question_repo = InterviewIndividualQuestionRepository(session)
        self.favorite_resume_repo = FavoriteResumeRepository(session)

    async def get_questions_by_resume(self, resume_id: int, session_id: str):
        questions = await self.interview_question_repo.get_questions_by_resume(resume_id, session_id)
        return questions

    async def create_individual_questions(self, question_text: str, resume_id: int, session_id: str, user_id: int) -> \
            Dict[str, Any]:
        db_resume = await self.favorite_resume_repo.get_favorite_resume_by_user_id(user_id=user_id, resume_id=resume_id,
                                                                                   session_id=session_id)
        if db_resume is None:
            raise NotFoundException(f"Resume with id {resume_id} not found")

        try:
            async with self.session:
                created_question = await self.interview_question_repo.create_question({
                    "question_text": question_text,
                    "resume_id": resume_id,
                    "session_id": session_id,
                })
                await self.session.commit()
            return {"question": created_question, "success": True}
        except Exception as e:
            await self.session.rollback()
            raise BadRequestException(f"Failed to create question: {str(e)}")

    async def delete_question(self, question_id: int) -> Dict[str, bool]:
        existing_question = await self.interview_question_repo.get_question_by_id(question_id)
        if not existing_question:
            raise NotFoundException("Question not found")

        try:
            async with self.session:
                await self.interview_question_repo.delete_question(question_id)
                await self.session.commit()
            return {"success": True}
        except Exception as e:
            await self.session.rollback()
            raise BadRequestException(f"Failed to delete question: {str(e)}")

    async def update_session_question(self, question_id: int, question_text: str) -> Dict[str, Any]:
        db_question = await self.interview_question_repo.get_question_by_id(question_id)
        if not db_question:
            raise NotFoundException("Question not found")

        update_data = {"question_text": question_text}
        try:
            async with self.session:
                updated_question = await self.interview_question_repo.update_question(question_id, update_data)
                await self.session.commit()
            return {"question": updated_question, "success": True}
        except Exception as e:
            await self.session.rollback()
            raise BadRequestException(f"Failed to update question: {str(e)}")
