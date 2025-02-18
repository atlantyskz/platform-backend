from fastapi import Depends, FastAPI,APIRouter, Form, WebSocket
from src.core.middlewares.auth_middleware import get_current_user
from src.core.factory import Factory
from src.controllers.hh import HHController 
from enum import Enum

hh_router = APIRouter(prefix='/api/v1/hh',tags=['HH'])


# Определяем Enum для статусов
class VacancyStatus(Enum):
    active = "active"
    archived = "archived"


@hh_router.get("/get_auth_url")
async def get_auth_url(
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.get_auth_url()


@hh_router.post("/authorize")
async def authorize(
    code:str,
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.auth_callback(current_user.get('sub'),code)

@hh_router.post("/refresh_token")
async def refresh_token(
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.refresh_token(current_user.get('sub'))

@hh_router.get("/hh_account_info")
async def hh_account_info(
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.get_hh_account_info(current_user.get('sub'))


@hh_router.get("/user_vacancies")
async def get_user_vacancies(
    status: str, 
    page: int = 0,
    current_user: dict = Depends(get_current_user),
    hh_controller: HHController = Depends(Factory.get_hh_controller)
):
    # Передаем статус в контроллер
    return await hh_controller.get_user_vacancies(current_user.get('sub'), status, page)


@hh_router.get("/user_vacancies")
async def get_user_vacancies(
    status:str = ['active','archived'],
    page:int = 0,
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.get_user_vacancies(current_user.get('sub'),status,page)


@hh_router.get("/vacancy/{vacancy_id}")
async def get_vacancy(
    vacancy_id:int,
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.get_vacancy_by_id(current_user.get('sub'),vacancy_id)


@hh_router.get("/vacancy/{vacancy_id}/applications")
async def get_vacancy_applications(
    vacancy_id:int,
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.get_vacancy_applicants(current_user.get('sub'),vacancy_id)

@hh_router.post("/vacancy/{vacancy_id}/analyze")
async def analyze_vacancy(
    vacancy_id:int,
    session_id: str = Form(...),
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.analyze_vacancy_applicants(session_id,current_user.get('sub'),vacancy_id)

@hh_router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.logout(current_user.get('sub'))


@hh_router.websocket("/ws/{vacancy_id}/progress")
async def websocket_endpoint(
    vacancy_id:str,
    websocket: WebSocket,
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    await hh_controller.websocket_endpoint(vacancy_id,websocket,current_user.get('sub'))