from fastapi import APIRouter, Depends
from sqlalchemy.util import await_only

from src.controllers.promocode import PromoCodeController
from src.core.factory import Factory
from src.core.middlewares.auth_middleware import get_current_user
from src.schemas.requests.promo_code import PromoCodeCreate, PromoCodeUpdate
from src.schemas.responses.subscription import PromoUsageAnalysis

promocode_router = APIRouter(prefix="/api/v1/promocode", tags=["Promo Code"])


@promocode_router.post("/generate")
async def generate_promocode(
        data: PromoCodeCreate,
        promocode_controller: PromoCodeController = Depends(Factory.get_promocode_controller),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await promocode_controller.generate_promocode(user_id, data.dict())


@promocode_router.get("/me")
async def get_my_promocode(
        promocode_controller: PromoCodeController = Depends(Factory.get_promocode_controller),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await promocode_controller.get_user_promo_code(user_id)


@promocode_router.put("/update/{user_id}")
async def update_promocode(
        user_id: int,
        data: PromoCodeUpdate,
        promocode_controller: PromoCodeController = Depends(Factory.get_promocode_controller)
):
    return await promocode_controller.update_promocode(user_id, data.dict())


@promocode_router.get("/analyze", response_model=PromoUsageAnalysis)
async def analyze_user_subscription(
        promo_controller: PromoCodeController = Depends(Factory.get_promocode_controller),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await promo_controller.analyze_promocode(user_id)


@promocode_router.get("/check/promocode/{promo_code}")
async def check_promocode(
        promo_code: str,
        promocode_controller: PromoCodeController = Depends(Factory.get_promocode_controller)
):
    return await promocode_controller.check_promocode(promo_code)