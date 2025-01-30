from pydantic import BaseModel



class TopUpBillingRequest(BaseModel):
    atl_amount: int
    payment_method: str
    discount_id: int|None = None

