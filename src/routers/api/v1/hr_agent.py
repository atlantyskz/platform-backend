import json
import uuid
from fastapi import APIRouter,Depends,File,UploadFile,Form
from httpx import AsyncClient, Timeout
from src.services.request_sender import RequestSender
from src.core.middlewares.auth_middleware import JWTBearer, get_current_user
from src.controllers.hr_agent import HRAgentController
from src.core.factory import Factory
from src.schemas.requests.users import *
from src.schemas.responses.auth import *
from typing import List, Optional


hr_agent_router = APIRouter(prefix='/api/v1/hr_agent',tags=['HR'])

@hr_agent_router.post("/generate_vacancy")
async def create_vacancy(
    file: Optional[UploadFile] = File(None), 
    vacancy_text: Optional[str] = Form(None), 
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    return await hr_agent_controller.create_vacancy(file,vacancy_text)
        
@hr_agent_router.post('/cv_analyzer')
async def cv_analyzer(
    current_user: int = Depends(get_current_user),
    session_id: Optional[uuid.UUID] = Form(None),
    vacancy_requirement: UploadFile = File(...),
    cv_files: List[UploadFile] = File(...),
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)
):
    if not session_id:
        session_id = None
    return await hr_agent_controller.cv_analyzer(current_user.get('sub'), session_id, vacancy_requirement, cv_files)

@hr_agent_router.get('/cv_analyzer/contexts_results/{session_id}')
async def get_contexts_results(session_id:str,hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)):
    return await hr_agent_controller.get_cv_analyzer_result_by_session_id(session_id)

@hr_agent_router.get('/cv_analyzer/export_to_csv/{session_id}')
async def get_contexts_results(session_id:str,hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)):
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