from fastapi import APIRouter,Depends, Form,UploadFile,File
from src.controllers.clone import CloneController
from src.core.factory import Factory
from src.schemas.requests.users import *
from src.schemas.responses.auth import *
from src.core.middlewares.auth_middleware import get_current_user
from src.core.middlewares.auth_middleware import require_roles
from src.models.role import RoleEnum


clone_router = APIRouter(prefix='/api/v1/clone',tags=['CLONE'])


@clone_router.post('/create')
async def create_clone(
    gender:str = Form(...),
    name:str = Form(...),
    lipsynch_text: str = Form(...),
    agreement_video:UploadFile = File(...),
    sample_video:UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    clone_service: CloneController = Depends(Factory.get_clone_controller)
):
    return await clone_service.create_clone(current_user.get('sub'),gender,name,lipsynch_text,agreement_video,sample_video)

@clone_router.get('/all')
@require_roles([RoleEnum.SUPER_ADMIN.value])
async def get_all(
    current_user: dict = Depends(get_current_user),
    clone_service: CloneController = Depends(Factory.get_clone_controller)
):
    return await clone_service.get_all_clone_requests()


@clone_router.get('/get_by_id/{clone_id}')
async def get_vidde_by_id(
    clone_id:int,
    video_type:str,
    current_user: dict = Depends(get_current_user),
    clone_service: CloneController = Depends(Factory.get_clone_controller)
):
    return await clone_service.stream_clone_video(clone_id,video_type)

@clone_router.get('/user')
async def get_user_clone_requests(
    current_user: dict = Depends(get_current_user),
    clone_service: CloneController = Depends(Factory.get_clone_controller)
):
    """
    Получает все запросы на клон для текущего пользователя.
    """
    return await clone_service.get_clone_requests_by_user(current_user.get('sub'))


@clone_router.put('/update/{clone_id}')
@require_roles([RoleEnum.SUPER_ADMIN.value])
async def update_clone_status(
    clone_id: int,
    new_status: str = Form(...),
    current_user: dict = Depends(get_current_user),
    clone_service: CloneController = Depends(Factory.get_clone_controller)
):
    """
    Обновляет статус запроса на клон.
    Только администратор может менять статус.
    """
    return await clone_service.update_clone_request_status(clone_id, new_status, is_admin=True)