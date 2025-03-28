from fastapi import APIRouter, Depends

from src.controllers.subs import SubsController
from src.core.factory import Factory

subs_router = APIRouter(prefix="/api/v1/subscription", tags=["Subscription"])


@subs_router.get("/all")
async def get_all_subscriptions(
        subs_controller: SubsController = Depends(Factory.get_subs_controller)
):
    return await subs_controller.get_all_subscriptions()


@subs_router.get("/{subscription_id}")
async def get_subscription_by_id(
        subscription_id: int,
        subs_controller: SubsController = Depends(Factory.get_subs_controller)
):
    return await subs_controller.get_subscription(subscription_id)