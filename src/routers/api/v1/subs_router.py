from fastapi import APIRouter, Depends

from src.controllers.subs import SubsController
from src.core.factory import Factory
from src.core.middlewares.auth_middleware import get_current_user

subs_router = APIRouter(prefix="/api/v1/subscription", tags=["Subscription"])


@subs_router.get("/all")
async def get_all_subscriptions(
        subs_controller: SubsController = Depends(Factory.get_subs_controller)
):
    return await subs_controller.get_all_subscriptions()

@subs_router.get("/user_active_subscription")
async def get_user_active_subscription(
        current_user: dict = Depends(get_current_user),
        subs_controller: SubsController = Depends(Factory.get_subs_controller)
):
    user_id = current_user.get("sub")
    return await subs_controller.get_user_active_subscriptions(user_id)

@subs_router.get("/{subscription_id}")
async def get_subscription_by_id(
        subscription_id: int,
        subs_controller: SubsController = Depends(Factory.get_subs_controller)
):
    return await subs_controller.get_subscription(subscription_id)

