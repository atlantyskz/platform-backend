from fastapi import APIRouter, Body,Depends,File, Query,UploadFile,Form, WebSocket
from httpx import AsyncClient, Timeout
from src.core.middlewares.auth_middleware import get_current_user,require_roles
from src.models.role import RoleEnum
from src.controllers.hr_agent import HRAgentController
from src.core.factory import Factory
from src.schemas.requests.users import *
from src.schemas.requests.vacancy import VacancyTextUpdate,VacancyTextCreate
from src.schemas.responses.auth import *
from typing import List, Optional


hr_agent_router = APIRouter(prefix='/api/v1/hr_agent',)

@hr_agent_router.post('/vacancy/create',tags=["HR VACANCY"])
async def create_vacancy(
    title:str = Form(...),
    vacancy_text:str = Form(None),
    vacancy_file:UploadFile = Form(None),
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
    current_user: dict = Depends(get_current_user),
):
    return await hr_agent_controller.create_vacancy(current_user.get('sub'),title, vacancy_file,vacancy_text)


@hr_agent_router.put("/vacancy/update/{vacancy_id}",tags=["HR VACANCY"])
@require_roles([RoleEnum.ADMIN,RoleEnum.EMPLOYER])
async def update_vacancy(
    vacancy_id:int,
    vacancy_text:VacancyTextUpdate,
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
    current_user: dict = Depends(get_current_user),
):
    attributes = vacancy_text.model_dump()
    return await hr_agent_controller.update_vacancy(current_user.get('sub'), vacancy_id, attributes)


@hr_agent_router.get("/vacancy/generated/user_vacancies", tags=["HR VACANCY"])
@require_roles([RoleEnum.ADMIN, RoleEnum.EMPLOYER])
async def get_generated_user_vacancies(
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
    current_user: dict = Depends(get_current_user),
):
    return await hr_agent_controller.get_user_vacancies(current_user.get('sub'))


@hr_agent_router.get("/vacancy/generated/{vacancy_id}",tags=["HR VACANCY"])
async def get_generated_user_vacancy(
    vacancy_id:int,
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
    current_user: dict = Depends(get_current_user),
):
    return await hr_agent_controller.get_generated_vacancy(vacancy_id)


@hr_agent_router.get('/resume_analyze/favorites/{session_id}',tags=["HR FAVORITE CANDIDATES"])
async def get_favorites_candidates_by_session_id(
    session_id:str,
    current_user: dict = Depends(get_current_user),
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.get_favorite_resumes(current_user.get('sub'),session_id)

@hr_agent_router.post('/resume_analyze/add_to_favorites/{resume_id}',tags=["HR FAVORITE CANDIDATES"])
async def get_favorites_candidates_by_session_id(
    resume_id:int,
    current_user: dict = Depends(get_current_user),
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.add_resume_to_favorites(current_user.get('sub'),resume_id)


@hr_agent_router.get('/resume_analyze/sessions',tags=["HR RESUME ANALYZER"])
async def get_user_sessions(
    current_user: dict = Depends(get_current_user),
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)
):
    return await hr_agent_controller.get_user_sessions(current_user.get('sub'))


@hr_agent_router.post('/resume_analyze',tags=["HR RESUME ANALYZER"])
async def cv_analyzer(
    current_user: dict = Depends(get_current_user),
    session_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    vacancy_requirement: UploadFile = File(...),
    cv_files: List[UploadFile] = File(...),
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)
):
    if not session_id:
        session_id = None
    return await hr_agent_controller.cv_analyzer(current_user.get('sub'), session_id, vacancy_requirement, cv_files, title)

@hr_agent_router.get('/resume_analyze/results/{session_id}',tags=["HR RESUME ANALYZER"])
async def get_session_results(
    session_id:str,
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(10, gt=0, le=100, description="Limit for pagination (max 100)"),
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.get_cv_analyzer_result_by_session_id(session_id,offset,limit)

@hr_agent_router.get('/resume_analyze/export_to_csv/{session_id}',tags=["HR RESUME ANALYZER"])
async def export_session_results(
    session_id:str,
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
    
@hr_agent_router.websocket("/ws/vacancy/ai_update/{vacancy_id}")
async def vacancy_ai_update(
    vacancy_id:int, 
    websocket:WebSocket,
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.ws_update_vacancy_by_ai(vacancy_id,websocket)


