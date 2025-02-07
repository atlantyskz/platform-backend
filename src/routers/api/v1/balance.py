from typing import Optional
from fastapi import APIRouter,Depends, Query
from src.core.factory import Factory
from src.schemas.requests.balance import *
from src.core.middlewares.auth_middleware import get_current_user
from src.schemas.requests.balance import TopupBalanceRequest
from src.controllers.balance import BalanceController
balance_router = APIRouter(prefix='/api/v1/balance',tags=['BALANCE'])




@balance_router.get('/get_balance')
async def get_balance(
    balance_controller:BalanceController = Depends(Factory.get_balance_controller),
    current_user: dict = Depends(get_current_user)
)-> dict:
    user_id = current_user.get('sub')
    return await balance_controller.get_balance(user_id=user_id)


@balance_router.get('/balance-usage')
async def get_balance_usage(
    assistant_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    balance_controller:BalanceController = Depends(Factory.get_balance_controller),
    current_user: dict = Depends(get_current_user)
    
):
    user_id = current_user.get('sub')
    return await balance_controller.get_balance_usage(user_id, assistant_id, start_date, end_date, limit, offset)

