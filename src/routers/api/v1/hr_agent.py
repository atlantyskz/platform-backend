import asyncio
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, Form, WebSocket, \
    WebSocketDisconnect
from httpx import AsyncClient, Timeout

from src.controllers.hr_agent import HRAgentController
from src.core.factory import Factory
from src.core.middlewares.auth_middleware import get_current_user, get_current_user_ws
from src.core.redis_cli import get_redis_client
from src.schemas.requests.assistant import RenameRequest
from src.schemas.requests.vacancy import VacancyTextUpdate
from src.services.websocket import manager as ws_manager

hr_agent_router = APIRouter(prefix='/api/v1/hr_agent', )


@hr_agent_router.post('/vacancy/create', tags=["HR VACANCY"])
async def create_vacancy(
        vacancy_text: str = Form(None),
        vacancy_file: UploadFile = Form(None),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
        current_user: dict = Depends(get_current_user),
):
    return await hr_agent_controller.create_vacancy(current_user.get('sub'), vacancy_file, vacancy_text)


@hr_agent_router.delete('/vacancy/delete/{session_id}', tags=["HR VACANCY"])
async def delete_vacancy(
        session_id: UUID,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
        current_user: dict = Depends(get_current_user),
):
    return await hr_agent_controller.delete_vacancy_by_session_id(session_id, current_user.get('sub'))


@hr_agent_router.put("/vacancy/update/{session_id}", tags=["HR VACANCY"])
async def update_vacancy(
        session_id: UUID,
        vacancy_text: VacancyTextUpdate,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
        current_user: dict = Depends(get_current_user),
):
    attributes = vacancy_text.model_dump()
    return await hr_agent_controller.update_vacancy(current_user.get('sub'), session_id, attributes)


@hr_agent_router.patch('/archive/session/add_to_archive/{session_id}', tags=["HR SESSION Archive"])
async def add_session_to_archive(
        session_id: UUID,
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.add_session_to_archive(current_user.get('sub'), session_id)


@hr_agent_router.patch('/archive/session/remove_from_archive/{session_id}', tags=["HR SESSION Archive"])
async def remove_session_from_archive(
        session_id: UUID,
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.remove_session_from_archive(current_user.get('sub'), session_id)


@hr_agent_router.patch('/archive/session/rename/{session_id}', tags=["HR SESSION Rename"])
async def rename_session(
        session_id: UUID,
        new_title: RenameRequest,
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.rename_session(current_user.get('sub'), session_id, new_title.new_title)


@hr_agent_router.get("/vacancy/generated/user_vacancies", tags=["HR VACANCY"])
async def get_generated_user_vacancies(
        is_archived: bool = Query(False, description="Filter by archived status"),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
        current_user: dict = Depends(get_current_user),
):
    return await hr_agent_controller.get_user_vacancies(current_user.get('sub'), is_archived)


@hr_agent_router.get("/vacancy/generated/{session_id}", tags=["HR VACANCY"])
async def get_generated_user_vacancy(
        session_id: UUID,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
        current_user: dict = Depends(get_current_user),
):
    return await hr_agent_controller.get_generated_vacancy(session_id)


@hr_agent_router.get('/resume_analyze/favorites/{session_id}', tags=["HR FAVORITE CANDIDATES"])
async def get_favorites_candidates_by_session_id(
        session_id: str,
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.get_favorite_resumes(current_user.get('sub'), session_id)


@hr_agent_router.get("/result/{resume_id}", tags=["HR FAVORITE CANDIDATES"])
async def get_result_data(
        resume_id: int,
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),

):
    result_data = await hr_agent_controller.fetch_result_data(resume_id)
    return {"resume_id": resume_id, "result_data": result_data}


@hr_agent_router.post("/generate_questions/{session_id}", tags=["HR FAVORITE CANDIDATES"])
async def generate_questions(
        session_id: str,
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    task_id = await hr_agent_controller.generate_questions_for_candidate(session_id, current_user.get('sub'))
    return {"task_id": task_id}

@hr_agent_router.post('/resume_analyze/add_to_favorites/{resume_id}', tags=["HR FAVORITE CANDIDATES"])
async def add_resume_to_favorites(
        resume_id: int,
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.add_resume_to_favorites(current_user.get('sub'), resume_id)


@hr_agent_router.delete('/resume_analyze/delete_from_favorites/{resume_id}', tags=["HR FAVORITE CANDIDATES"])
async def delete_from_favorites(
        resume_id: int,
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.delete_from_favorites(current_user.get('sub'), resume_id)


@hr_agent_router.get('/resume_analyze/sessions', tags=["HR SESSIONS"])
async def get_user_sessions(
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)
):
    return await hr_agent_controller.get_user_sessions(current_user.get('sub'))


@hr_agent_router.delete('/resume_analyze/sessions/{session_id}', tags=["HR SESSION DELETE"])
async def delete_user_sessions(
        session_id: UUID,
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)
):
    return await hr_agent_controller.delete_session(session_id)


connections = {}


@hr_agent_router.websocket("/ws/progress-handling-files/{user_id}")
async def websocket_progress(websocket: WebSocket, user_id: int):
    await websocket.accept()
    connections[user_id] = websocket  # Сохраняем соединение для пользователя
    try:
        while True:
            await asyncio.sleep(5)  # Просто удерживаем соединение открытым
    except WebSocketDisconnect:
        connections.pop(user_id, None)  # Удаляем соединение при отключении клиента


@hr_agent_router.post('/resume_analyzer/session_creator', tags=["HR SESSIONS"])
async def session_creator(
        current_user: dict = Depends(get_current_user),
        title: str = Form(...),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)

):
    return await hr_agent_controller.session_creator(current_user.get('sub'), title)


@hr_agent_router.get("/tasks/{task_id}/preview", tags=["HR RESUME ANALYZER"])
async def preview_candidate_cv(
        task_id: str,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.preview_cv(task_id)


@hr_agent_router.post('/resume_analyze', tags=["HR RESUME ANALYZER"])
async def cv_analyzer(
        current_user: dict = Depends(get_current_user),
        session_id: str = Form(...),
        vacancy_requirement: UploadFile = File(None),
        vacancy_requirement_text: Optional[str] = Form(None),
        cv_files: List[UploadFile] = File(...),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    if not session_id:
        session_id = None

    user_id = current_user.get('sub')
    total_files = len(cv_files)
    manager = ws_manager

    # Отправляем начальное сообщение о старте загрузки
    if manager:
        await manager.send_json(user_id, {
            "type": "start",
            "total_files": total_files,
            "message": "Начинаю обработку файлов"
        })

    for index, file in enumerate(cv_files, start=1):
        if manager:
            await manager.send_json(user_id, {
                "type": "progress",
                "processed_files": index,
                "total_files": total_files,
                "message": f"Принял {index}/{total_files} файлов"
            })

    if manager:
        await manager.send_json(user_id, {
            "type": "complete",
            "message": "Все файлы успешно обработаны"
        })

    return await hr_agent_controller.cv_analyzer(current_user.get('sub'), session_id, vacancy_requirement,
                                                 vacancy_requirement_text, cv_files, )


# return await hr_agent_controller.cv_analyzer(current_user.get('sub'), session_id, vacancy_requirement,vacancy_requirement_text, cv_files, title)

@hr_agent_router.delete('/resume_analyze/{session_id}', tags=["HR RESUME ANALYZER"])
async def delete_resume(
        session_id: str,
        current_user: dict = Depends(get_current_user),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)
):
    return await hr_agent_controller.delete_resume_by_session_id(current_user.get('sub'), session_id)


@hr_agent_router.get('/resume_analyze/results/{session_id}', tags=["HR RESUME ANALYZER"])
async def get_session_results(
        session_id: str,
        offset: int = Query(0, ge=0, description="Offset for pagination"),
        limit: int = Query(10, gt=0, le=100, description="Limit for pagination (max 100)"),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
        current_user: dict = Depends(get_current_user),
):
    return await hr_agent_controller.get_cv_analyzer_result_by_session_id(session_id, current_user.get('sub'), offset,
                                                                          limit)


@hr_agent_router.get('/resume_analyze/export_to_csv/{session_id}', tags=["HR RESUME ANALYZER"])
async def export_session_results(
        session_id: str,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
        current_user: dict = Depends(get_current_user),
):
    return await hr_agent_controller.export_to_csv(session_id)


@hr_agent_router.get('/cv')
async def make_request():
    async with AsyncClient(timeout=Timeout(30.0, read=30.0)) as client:
        res = await client.post(
            url='http://llm_service:8001/hr/analyze_cv_by_vacancy',
            json={
                'vacancy_text': "Джун нужен",
                'cv_text': "php dev"
            }
        )
        return res.json()


@hr_agent_router.websocket("/ws/vacancy/ai_update/{session_id}")
async def vacancy_ai_update(
        session_id: str,
        websocket: WebSocket,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.ws_update_vacancy_by_ai(session_id, websocket)


@hr_agent_router.websocket('/ws/resume_analyze/{session_id}')
async def resume_analyzer_chat(
        session_id: str,
        websocket: WebSocket,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
        current_user: dict = Depends(get_current_user_ws),
):
    return await hr_agent_controller.ws_review_results_by_ai(session_id, websocket, current_user.get('sub'))


@hr_agent_router.post("/generate-pdf/{session_id}", tags=["VACANCY PDF GENERATOR"])
async def generate_pdf(
        session_id: UUID,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.generate_pdf(session_id)


@hr_agent_router.websocket("/ws/progress/{user_id}")
async def websocket_endpoint(
        websocket: WebSocket,
        user_id: int,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    await hr_agent_controller.ws_progress(websocket, user_id)


@hr_agent_router.websocket("/ws/upload_progress/{user_id}")
async def upload_progress_websocket(
        websocket: WebSocket, user_id: int,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)
):
    await websocket.accept()
    try:
        while True:
            # Здесь сервер может отправлять обновления прогресса загрузки
            progress_data = hr_agent_controller.get_upload_progress(user_id)
            await websocket.send_json(progress_data)
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected from upload progress tracking")


@hr_agent_router.websocket("/ws/task_status/{task_id}")
async def websocket_task_status(
        websocket: WebSocket,
        task_id: str,
        redis=Depends(get_redis_client)):
    await websocket.accept()
    try:
        while True:
            status = await redis.get(task_id)
            if status is None:
                await websocket.send_json({
                    "task_id": task_id,
                    "status": "failed",
                })
                await redis.delete(task_id)
                break

            await websocket.send_json({
                "task_id": task_id,
                "status": status,
            })

            if status in ["failed", "success"]:
                break

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        print(f"Client disconnected from task_id={task_id}")
    finally:
        await websocket.close()


@hr_agent_router.get("/preview/session/tasks/{session_id}")
async def get_session_task(
        session_id: str,
        redis=Depends(get_redis_client),
        user=Depends(get_current_user),
):
    return await redis.get(f"task:{user.get('sub')}:{session_id}")
