from pydantic import BaseModel

from src.schemas.responses.user_sub import UserSubResponseSchema


class PromoUsageAnalysis(BaseModel):
    count: int
    total_price: float
    items: list[UserSubResponseSchema]
