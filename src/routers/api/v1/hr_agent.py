import json
from fastapi import APIRouter,Depends,File,UploadFile,Form
from src.services.request_sender import RequestSender
from src.core.middlewares.auth_middleware import JWTBearer
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
    context_id: Optional[str] = Form(None),
    vacancy_requirement: UploadFile = File(...),
    cv_files: List[UploadFile] = File(...),
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)
):
    return await hr_agent_controller.cv_analyzer(context_id, vacancy_requirement, cv_files)

@hr_agent_router.get('/cv_analyzer/contexts_results/{context_id}')
async def get_contexts_results(context_id:str,hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller)):
    return await hr_agent_controller.get_cv_analyzer_result_by_context_id(context_id)



@hr_agent_router.post('/cv')
async def cv(data: dict):
    req_sender = RequestSender()
    response_data = await req_sender._send_request(data)
    return (response_data)