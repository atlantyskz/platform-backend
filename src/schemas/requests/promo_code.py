from pydantic import BaseModel


class PromoCodeCreate(BaseModel):
    name: str
    email: str
    phone_number: str


class PromoCodeUpdate(BaseModel):
    is_active: bool
