from datetime import datetime

from pydantic import BaseModel


class UserSubResponseSchema(BaseModel):
    id: int
    user_id: int
    subscription_id: int
    promo_id: int
    bought_date: datetime