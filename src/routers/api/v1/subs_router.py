from fastapi import APIRouter, Depends

from src.controllers.subscription_plan import SubscriptionPlanController
from src.core.factory import Factory
from src.core.middlewares.auth_middleware import get_current_user

subs_router = APIRouter(prefix="/api/v1/subscriptions", tags=["Subscription"])


@subs_router.get("")
async def get_all_subscriptions(
        subs_controller: SubscriptionPlanController = Depends(Factory.get_subscription_plan_controller)
):
    return await subs_controller.get_all_subscriptions()


@subs_router.get("/active-subscription")
async def get_active_subscription(
        current_user: dict = Depends(get_current_user),
        subs_controller: SubscriptionPlanController = Depends(Factory.get_subscription_plan_controller)
):
    user_id = current_user.get("sub")
    return await subs_controller.get_organization_active_subscription(user_id)
