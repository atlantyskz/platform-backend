from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundException, BadRequestException
from src.repositories.assistant_session import AssistantSessionRepository
from src.repositories.interview_common_question import InterviewCommonQuestionRepository


class InterviewCommonQuestionController:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.interview_question_repo = InterviewCommonQuestionRepository(session)
        self.assistant_session_repo = AssistantSessionRepository(session)

    async def _validate_session(self, session_id: str, user_id: int):
        db_assistant_session = await self.assistant_session_repo.get_by_session_id(session_id, user_id)
        if db_assistant_session is None:
            raise NotFoundException("Assistant session not found")

        return db_assistant_session

    async def get_session_questions(self, session_id: str, user_id: int):
        await self._validate_session(session_id, user_id)

        questions = await self.interview_question_repo.get_session_questions(session_id)
        return questions

    async def create_session_question(self, session_id: str, question_text: str, user_id: int) -> Dict[str, Any]:
        await self._validate_session(session_id, user_id)

        try:
            async with self.session:
                created_question = await self.interview_question_repo.create_question({
                    "question_text": question_text,
                    "session_id": session_id
                })
                await self.session.commit()

                return {"question": created_question, "success": True}
        except Exception as e:
            raise BadRequestException(f"Failed to create question: {str(e)}")

    async def delete_session_question(self, question_id: int) -> Dict[str, bool]:
        existing_question = await self.interview_question_repo.get_question_by_id(question_id)
        if not existing_question:
            raise NotFoundException("Question not found")

        try:
            async with self.session:
                await self.interview_question_repo.delete_question(question_id)
                await self.session.commit()
            return {"success": True}
        except Exception as e:
            raise BadRequestException(f"Failed to delete question: {str(e)}")

    async def update_session_question(self, question_id: int, question_text: str) -> Dict[str, Any]:
        db_question = await self.interview_question_repo.get_question_by_id(question_id)
        if not db_question:
            raise NotFoundException("Question not found")

        try:
            async with self.session:
                await self.interview_question_repo.update_question(
                    question_id,
                    {"question_text": question_text}
                )
                await self.session.commit()
            return {"success": True}
        except Exception as e:
            raise BadRequestException(f"Failed to update question: {str(e)}")
