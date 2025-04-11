from typing import List

from fastapi import APIRouter, Depends
from starlette.websockets import WebSocket, WebSocketDisconnect

from src.controllers.interview_individual_question import InterviewIndividualQuestionController
from src.core.factory import Factory
from src.core.middlewares.auth_middleware import get_current_user
from src.schemas.requests.interview_questions import InterviewIndividualQuestions, InterviewIndividualQuestionsUpdate
from src.schemas.responses.interview_questions import InterviewQuestionsSchema
from src.services.websocket import manager

interview_individual_question_router = APIRouter(
    prefix='/api/v1/first-call/individual-questions',
    tags=['FIRST CALL INDIVIDUAL QUESTION']
)


@interview_individual_question_router.get('/', response_model=List[InterviewQuestionsSchema])
async def get_interview_individual_question(
        resume_id: int,
        interview_controller: InterviewIndividualQuestionController = Depends(
            Factory.get_individual_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.get_questions_by_resume(resume_id=resume_id)


@interview_individual_question_router.post('/')
async def create_individual_question(
        form: InterviewIndividualQuestions,
        interview_controller: InterviewIndividualQuestionController = Depends(
            Factory.get_individual_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.create_individual_question(
        question_text=form.question_text,
        resume_id=form.resume_id
    )


@interview_individual_question_router.delete('/{question_id}')
async def delete_question(
        question_id: int,
        interview_controller: InterviewIndividualQuestionController = Depends(
            Factory.get_individual_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.delete_question(
        question_id=question_id
    )


@interview_individual_question_router.put('/{question_id}')
async def update_question(
        question_id: int,
        form: InterviewIndividualQuestionsUpdate,
        interview_controller: InterviewIndividualQuestionController = Depends(
            Factory.get_individual_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.update_individual_question(
        question_id=question_id,
        question_text=form.question_text
    )


@interview_individual_question_router.post('/generate-questions/{session_id}')
async def generate_question(
        session_id: str,
        interview_controller: InterviewIndividualQuestionController = Depends(
            Factory.get_individual_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.generate_question(session_id, user.get("sub"))


@interview_individual_question_router.get("/progress/{session_id}")
async def get_progress_from_db(
        session_id: str,
        interview_controller: InterviewIndividualQuestionController = Depends(
            Factory.get_individual_question_controller
        ),
        user=Depends(get_current_user)
):
    return await interview_controller.get_progress_from_db(session_id, user.get("sub"))


@interview_individual_question_router.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    await websocket.accept()
    manager.session_connect(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        del manager[session_id]
