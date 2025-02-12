from fastapi import Depends, FastAPI,APIRouter
from src.core.middlewares.auth_middleware import get_current_user
from src.core.factory import Factory
from src.controllers.hh import HHController 

hh_router = APIRouter(prefix='/api/v1/hh',tags=['HH'])

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
    status:str|None = None,
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.get_user_vacancies(current_user.get('sub'),status)


@hh_router.get("/vacancy/{vacancy_id}")
async def get_vacancy(
    vacancy_id:int,
    current_user: dict = Depends(get_current_user),
    hh_controller:HHController = Depends(Factory.get_hh_controller)
):
    return await hh_controller.get_vacancy_by_id(current_user.get('sub'),vacancy_id)