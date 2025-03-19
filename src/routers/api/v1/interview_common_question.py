from typing import List

from fastapi import APIRouter, Depends

from src.controllers.interview_common_question import InterviewCommonQuestionController
from src.core.factory import Factory
from src.core.middlewares.auth_middleware import get_current_user
from src.schemas.requests.interview_questions import InterviewCommonQuestions, InterviewCommonQuestionsUpdate
from src.schemas.responses.interview_questions import InterviewQuestionsSchema

interview_common_question_router = APIRouter(prefix='/api/v1/first-call/common-questions',
                                             tags=['FIRST CALL COMMON QUESTION'])


@interview_common_question_router.get('/{session_id}', response_model=List[InterviewQuestionsSchema])
async def get_interview_common_question(
        session_id: str,
        interview_controller: InterviewCommonQuestionController = Depends(
            Factory.get_common_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.get_session_questions(session_id, user_id=user.get("sub"))


@interview_common_question_router.post('/')
async def create_interview_common_question(
        form: InterviewCommonQuestions,
        interview_controller: InterviewCommonQuestionController = Depends(
            Factory.get_common_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.create_session_question(
        form.session_id, form.question_text, user_id=user.get("sub")
    )


@interview_common_question_router.put('/{question_id}')
async def update_interview_common_question(
        question_id: int,
        form: InterviewCommonQuestionsUpdate,
        interview_controller: InterviewCommonQuestionController = Depends(
            Factory.get_common_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.update_session_question(
        question_id, form.question_text
    )


@interview_common_question_router.delete('/{question_id}')
async def delete_interview_common_question(
        question_id: int,
        interview_controller: InterviewCommonQuestionController = Depends(
            Factory.get_common_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.delete_session_question(question_id)
