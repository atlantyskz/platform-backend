from fastapi import APIRouter,Depends, Form,UploadFile,File
from src.controllers.clone import CloneController
from src.core.factory import Factory
from src.schemas.requests.users import *
from src.schemas.responses.auth import *
from src.core.middlewares.auth_middleware import get_current_user


clone_router = APIRouter(prefix='/api/v1/clone',tags=['CLONE'])


@clone_router.post('/create')
async def create_clone(
    lipsynch_text: str = Form(...),
    agreement_video:UploadFile = File(...),
    sample_video:UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    clone_service: CloneController = Depends(Factory.get_clone_controller)
):
    return await clone_service.create_clone(current_user.get('sub'),lipsynch_text,agreement_video,sample_video)

@clone_router.get('/all')
async def get_all(
    clone_service: CloneController = Depends(Factory.get_clone_controller)
):
    return await clone_service.get_all_clone_requests()


@clone_router.get('/get_by_id/{id}')
async def get_by_id(
    id:int,
    clone_service: CloneController = Depends(Factory.get_clone_controller)
):
    return await clone_service.