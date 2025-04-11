from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundException, BadRequestException
from src.core.tasks import generate_questions_task
from src.models import InterviewIndividualQuestion, GenerateStatus
from src.repositories import AssistantSessionRepository, AssistantRepository, OrganizationRepository, BalanceRepository
from src.repositories.favorite_resume import FavoriteResumeRepository
from src.repositories.interview_individual_question import InterviewIndividualQuestionRepository
from src.repositories.question_generate_session import QuestionGenerateSessionRepository


class InterviewIndividualQuestionController:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.interview_question_repo = InterviewIndividualQuestionRepository(session)
        self.favorite_resume_repo = FavoriteResumeRepository(session)
        self.session_repository = AssistantSessionRepository(session)
        self.question_generate_session_repository = QuestionGenerateSessionRepository(session)
        self.assistant_repo = AssistantRepository(session)
        self.organization_repo = OrganizationRepository(session)
        self.balance_repo = BalanceRepository(session)

    async def get_questions_by_resume(self, resume_id: int) -> list[InterviewIndividualQuestion]:
        resume = await self.favorite_resume_repo.get_resume(resume_id)
        if not resume:
            raise NotFoundException("Resume not found")
        return await self.interview_question_repo.get_questions_by_resume(resume_id)

    async def create_individual_question(self, question_text: str, resume_id: int) -> Dict[str, Any]:
        resume = await self.favorite_resume_repo.get_resume(resume_id)
        if not resume:
            raise NotFoundException("Resume not found")

        try:
            created_question = await self.interview_question_repo.create_question({
                "question": question_text,
                "resume_id": resume_id
            })
            await self.session.commit()
            return {"question": created_question, "success": True}
        except Exception as e:
            await self.session.rollback()
            raise BadRequestException(f"Failed to create question: {e}")

    async def delete_question(self, question_id: int) -> Dict[str, bool]:
        question = await self.interview_question_repo.get_question_by_id(question_id)
        if not question:
            raise NotFoundException("Question not found")

        try:
            await self.interview_question_repo.delete_question(question_id)
            await self.session.commit()
            return {"success": True}
        except Exception as e:
            await self.session.rollback()
            raise BadRequestException(f"Failed to delete question: {e}")

    async def update_individual_question(self, question_id: int, question_text: str) -> Dict[str, Any]:
        question = await self.interview_question_repo.get_question_by_id(question_id)
        if not question:
            raise NotFoundException("Question not found")

        try:
            updated_question = await self.interview_question_repo.update_question(
                question_id, {"question": question_text}
            )
            await self.session.commit()
            return {"question": updated_question, "success": True}
        except Exception as e:
            await self.session.rollback()
            raise BadRequestException(f"Failed to update question: {e}")

    async def generate_question(self, session_id: str, user_id: int) -> Dict[str, Any]:
        db_session = await  self.session_repository.get_by_session_id(session_id, user_id)
        if not db_session:
            raise NotFoundException("Session not found")

        db_session = await self.question_generate_session_repository.get_by_session_id(session_id)
        if db_session and (db_session.status in (GenerateStatus.PENDING, GenerateStatus.SUCCESS)):
            raise BadRequestException("Session already exists")
        assistant = await self.assistant_repo.get_assistant_by_name("ИИ Рекрутер")
        organization = await self.organization_repo.get_user_organization(user_id)
        if not organization:
            raise NotFoundException("Organization not found")
        user_balance = await self.balance_repo.get_balance(organization.id)

        await self.question_generate_session_repository.create(session_id)
        generate_questions_task.delay(
            session_id,
            user_id,
            assistant.id,
            organization.id,
            user_balance.id
        )
        return {"success": True}

    async def get_progress_from_db(self, session_id: str, user_id) -> Dict[str, Any]:
        db_session = await self.session_repository.get_by_session_id(session_id, user_id)
        if not db_session:
            raise NotFoundException("Session not found")

        db_generate_session = await self.question_generate_session_repository.get_by_session_id(session_id)
        if not db_generate_session:
            raise NotFoundException("Interview question generate session not found")
        resumes = await self.favorite_resume_repo.get_favorite_resumes_by_session_id(session_id)
        total = len(resumes)

        if total == 0:
            raise BadRequestException("No resumes found for this session")

        completed = 0
        for resume in resumes:
            questions = await self.interview_question_repo.get_questions_by_resume(resume.resume_id)
            if questions:
                completed += 1

        percentage = round(completed / total * 100)
        payload = {
            "session_id": session_id,
            "status": db_generate_session.status,
            "result": {
                "session_id": session_id,
                "total": total,
                "completed": completed,
                "percentage": percentage,
            }
        }
        return payload
