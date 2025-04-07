from fastapi import APIRouter, Depends

from src.controllers.bank_card import BankCardController, BankCardDTO
from src.core.factory import Factory
from src.core.middlewares.auth_middleware import get_current_user
from src.schemas.requests.bank_card import BankCardCreate, BankCardResponse

bank_card_router = APIRouter(prefix="/api/v1/bank-card", tags=["BANK CARD"])


@bank_card_router.post("/", response_model=BankCardResponse)
async def add_or_update_bank_card(
        card: BankCardCreate,
        bank_card_controller: BankCardController = Depends(Factory.get_bank_card_controller),
        current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await bank_card_controller.upsert_bank_card(user_id=user_id, card=BankCardDTO(
        card_number=card.card_number
    ))


@bank_card_router.get("/", response_model=BankCardResponse)
async def get_bank_card(
        bank_card_controller: BankCardController = Depends(Factory.get_bank_card_controller),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub")
    return await bank_card_controller.get_bank_card(user_id)
