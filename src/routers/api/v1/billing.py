from typing import Annotated, Optional
from fastapi import APIRouter, Body,Depends, File, Form, Query, UploadFile

from src.models.role import RoleEnum
from src.core.factory import Factory
from src.schemas.requests.balance import *

from src.core.middlewares.auth_middleware import get_current_user,require_roles
from src.schemas.requests.billing import TopUpBillingRequest
from src.controllers.billing import BillingController


billing_router = APIRouter(prefix='/api/v1/balance',tags=['BILLING'])

@billing_router.post('/topup')
async def topup_balance(
    billing_request: TopUpBillingRequest,
    billing_controller: BillingController = Depends(Factory.get_billing_controller),
    current_user: dict = Depends(get_current_user)
)-> dict:
    user_id = current_user.get('sub')
    return await billing_controller.top_up_balance(user_id, billing_request)

@billing_router.post('/billing-status')
async def billing_status(
    data: dict,
    billing_controller: BillingController = Depends(Factory.get_billing_controller),
):
    return await billing_controller.billing_status(data)

@billing_router.post('/failure-status')
async def failure_status(
    data: dict,
    billing_controller: BillingController = Depends(Factory.get_billing_controller),
):
    return await billing_controller.failure_status(data)

@billing_router.get('/transactions')
async def get_billing_transactions(
    status: Optional[str] = Query(None),
    limit: int = Query(10, ge=1),  
    offset: int = Query(0, ge=0), 
    billing_controller: BillingController = Depends(Factory.get_billing_controller),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get('sub')
    return await billing_controller.get_all_billing_transactions_by_organization_id(
        user_id, status, limit, offset
    )

@billing_router.post('/refund/{transaction_id}')
async def refund_transaction(
    transaction_id: int,
    access_token: str = Query(...),
    billing_controller: BillingController = Depends(Factory.get_billing_controller),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get('sub')
    return await billing_controller.refund_billing_transaction(access_token,user_id, transaction_id)


@billing_router.post('/refund_application')
async def refund_application(
    transaction_id:  Annotated[int, Form()],
    email:  Annotated[str, Form()],
    reason:  Annotated[str, Form()],
    file: UploadFile = File(None),    
    billing_controller: BillingController = Depends(Factory.get_billing_controller),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get('sub')
    return await billing_controller.refund_application_create(user_id, transaction_id,email,reason, file)

@billing_router.get('/refund_applications')
@require_roles([RoleEnum.SUPER_ADMIN.value])
async def get_refund_applications(
    status: Optional[str] = Query(None),
    limit: int |None  = Query(None, ge=1),  
    offset: int = Query(None, ge=0), 
    billing_controller: BillingController = Depends(Factory.get_billing_controller),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get('sub')
    return await billing_controller.get_refunds_application(user_id, status, limit, offset)

@billing_router.patch('/refund_application/{refund_id}')
@require_roles([RoleEnum.SUPER_ADMIN.value])
async def update_refund_application(
    refund_id: int,
    status: str = Form(...),
    billing_controller: BillingController = Depends(Factory.get_billing_controller),
    current_user: dict = Depends(get_current_user)
):
    return await billing_controller.update_refund_application(refund_id, status)