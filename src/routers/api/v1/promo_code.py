from fastapi import APIRouter, Depends

from src.controllers.promocode import PromoCodeController
from src.core.factory import Factory
from src.core.middlewares.auth_middleware import get_current_user
from src.schemas.requests.promo_code import PromoCodeCreate, PromoCodeUpdate

promo_code_router = APIRouter(prefix="/api/v1/promo-code", tags=["Promo Code"])


@promo_code_router.post("/get")
async def generate_promo_code(
        data: PromoCodeCreate,
        promo_code_controller: PromoCodeController = Depends(Factory.get_promo_code_controller),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await promo_code_controller.generate_promo_code(user_id, data.dict())


@promo_code_router.get("/me")
async def get_my_promo_code(
        promo_code_controller: PromoCodeController = Depends(Factory.get_promo_code_controller),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await promo_code_controller.get_user_promo_code(user_id)


@promo_code_router.put("/update/{user_id}")
async def update_promo_code(
        user_id: int,
        data: PromoCodeUpdate,
        promo_code_controller: PromoCodeController = Depends(Factory.get_promo_code_controller),
):
    return await promo_code_controller.update_promo_code(user_id, data.dict())


@promo_code_router.get("/analyze")
async def analyze_user_subscription(
        promo_code_controller: PromoCodeController = Depends(Factory.get_promo_code_controller),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await promo_code_controller.analyze_promo_code(user_id)


@promo_code_router.get("/promo-code/{promo_code}")
async def promo_code_information(
        promo_code: str,
        promo_code_controller: PromoCodeController = Depends(Factory.get_promo_code_controller),
):
    return await promo_code_controller.check_promo_code(promo_code)
