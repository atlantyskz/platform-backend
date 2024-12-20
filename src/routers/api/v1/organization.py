from fastapi import APIRouter,Depends,File, Request,UploadFile,Form
from src.core.middlewares.auth_middleware import JWTBearer
from src.models.role import RoleEnum
from src.controllers.organization import OrganizationController
from src.schemas.requests.organization import CreateOrganizationRequest,UpdateOrganizationRequest
from src.core.factory import Factory
from src.schemas.requests.users import *
from src.schemas.responses.auth import *
from typing import Optional

from src.core.middlewares.auth_middleware import get_current_user,require_roles


organization_router = APIRouter(prefix='/api/v1/organization',tags=['ORGANIZATION'])

@organization_router.post("/create/organization")
@require_roles([RoleEnum.ADMIN.value])
async def create_organization(
    create_organization_request:CreateOrganizationRequest,
    current_user:dict = Depends(get_current_user),
    organization_controller:OrganizationController = Depends(Factory.get_organization_controller)
):
    data = create_organization_request.model_dump()
    organization = await organization_controller.create_organization(**data,admin_id=current_user.get('sub'))
    return organization

@organization_router.patch('/update/organization')
@require_roles([RoleEnum.ADMIN.value])
async def update_organization(
    update_organization_request: UpdateOrganizationRequest,
    current_user:dict = Depends(get_current_user),
    organization_controller:OrganizationController = Depends(Factory.get_organization_controller),
):
    attributes = update_organization_request.model_dump(exclude_unset=True)
    return await organization_controller.update_organization(attributes, current_user.get('sub'))