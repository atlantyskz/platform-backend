from fastapi import APIRouter,Depends,File, Request,UploadFile,Form
from src.core.middlewares.auth_middleware import JWTBearer, require_roles
from src.controllers.organization_member import OrganizationMemberController
from src.schemas.requests.organization_member import CreateOrganizationMemberRequest,UpdateOrganizationMemberRequest
from src.core.factory import Factory
from src.schemas.requests.users import *
from src.schemas.responses.auth import *
from src.models.role import RoleEnum
from src.core.middlewares.auth_middleware import get_current_user


organization_member_router = APIRouter(prefix='/api/v1/organization_member',tags=['ORGANIZATION MEMBER'])


@organization_member_router.post('/create_member')
@require_roles([RoleEnum.ADMIN.value])
async def create_organization_member(
    create_member_request: CreateOrganizationMemberRequest,
    org_member_controller: OrganizationMemberController = Depends(Factory.get_org_member_controller),
    current_user: dict = Depends(get_current_user)  
):
    attributes = create_member_request.model_dump()
    return await org_member_controller.create_organization_member(attributes, current_user.get('sub'))

@organization_member_router.get("/get_organization_members/{organization_id}")
@require_roles([RoleEnum.ADMIN.value])
async def get_organization_members_by_org_id(
    organization_id:int,
    org_member_controller: OrganizationMemberController = Depends(Factory.get_org_member_controller),
    current_user: dict = Depends(get_current_user) 
):
    members = await org_member_controller.get_all_members_by_org_id(organization_id)
    return members

@organization_member_router.delete('/delete_employee/{employee_id}')
@require_roles([RoleEnum.ADMIN.value])
async def delete_employee(
    employee_id:int,
    org_member_controller: OrganizationMemberController = Depends(Factory.get_org_member_controller),
    current_user: dict = Depends(get_current_user)  
):
    return await org_member_controller.delete_member_from_organization(employee_id)


@organization_member_router.patch('/update_employee/')
@require_roles([RoleEnum.ADMIN.value])
async def update_employee(
    update_member_request:UpdateOrganizationMemberRequest,
    org_member_controller: OrganizationMemberController = Depends(Factory.get_org_member_controller),
    current_user: dict = Depends(get_current_user)  
):
    attributes = update_member_request.model_dump()
    admin_id = current_user.get('sub')
    return await org_member_controller.update_user(attributes, admin_id)