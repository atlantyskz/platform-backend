from fastapi import APIRouter, Depends
from src.core.middlewares.auth_middleware import get_current_user,require_roles
from src.models.role import RoleEnum
from src.controllers.assistant import AssistantController
from src.core.factory import Factory

assistant_router = APIRouter(prefix='/api/v1/assistants',tags=['ASSISTANT'])

@assistant_router.post('/add_to_organization/{assistant_id}')
@require_roles([RoleEnum.ADMIN])
async def add_assistant_to_organization(
    assistant_id: int,
    assistant_controller:AssistantController = Depends(Factory.get_assistant_controller),
    current_user:dict = Depends(get_current_user)
):
    return await assistant_controller.add_assistant_to_organization(current_user.get('sub'),assistant_id)

@assistant_router.delete('/delete_from_organization/{assistant_id}')
@require_roles([RoleEnum.ADMIN])
async def delete_from_organization(
    assistant_id: int,
    assistant_controller:AssistantController = Depends(Factory.get_assistant_controller),
    current_user:dict = Depends(get_current_user)
):
    return await assistant_controller.delete_from_organization(current_user.get('sub'),assistant_id)

@assistant_router.get('/get_all_assistants')
@require_roles([RoleEnum.ADMIN,RoleEnum.EMPLOYER])
async def get_all_assistants(
    assistant_controller: AssistantController = Depends(Factory.get_assistant_controller),
    current_user:dict = Depends(get_current_user)
):
    return await assistant_controller.get_all_assistants()
