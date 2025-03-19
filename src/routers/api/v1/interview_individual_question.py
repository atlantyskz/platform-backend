from typing import List

from fastapi import APIRouter, Depends

from src.controllers.interview_individual_question import InterviewIndividualQuestionController
from src.core.factory import Factory
from src.core.middlewares.auth_middleware import get_current_user
from src.schemas.requests.interview_questions import InterviewIndividualQuestions, InterviewIndividualQuestionsUpdate
from src.schemas.responses.interview_questions import InterviewQuestionsSchema

interview_individual_question_router = APIRouter(prefix='/api/v1/first-call/individual-questions',
                                                 tags=['FIRST CALL INDIVIDUAL QUESTION'])


@interview_individual_question_router.get('/', response_model=List[InterviewQuestionsSchema])
async def get_interview_individual_question(
        resume_id: int,
        session_id: str,
        interview_controller: InterviewIndividualQuestionController = Depends(
            Factory.get_individual_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.get_questions_by_resume(resume_id=resume_id, session_id=session_id)


@interview_individual_question_router.post('/')
async def create_individual_question(
        form: InterviewIndividualQuestions,
        interview_controller: InterviewIndividualQuestionController = Depends(
            Factory.get_individual_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.create_individual_questions(
        question_text=form.question_text,
        resume_id=form.resume_id,
        session_id=str(form.session_id),
        user_id=user.get("sub")
    )


@interview_individual_question_router.delete('/{question_id}')
async def delete_question(
        question_id: int,
        interview_controller: InterviewIndividualQuestionController = Depends(
            Factory.get_individual_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.delete_question(question_id=question_id)


@interview_individual_question_router.put('/{question_id}')
async def update_question(
        question_id: int,
        form: InterviewIndividualQuestionsUpdate,
        interview_controller: InterviewIndividualQuestionController = Depends(
            Factory.get_individual_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.update_session_question(
        question_id=question_id, question_text=form.question_text
    )
