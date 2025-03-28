from pydantic import BaseModel



class TopUpBillingRequest(BaseModel):
    atl_amount: float
    access_token: str
    invoice_id: str


class BuySubscription(BaseModel):
    subscription_id: int
    promo_code: str
    access_token: str
    invoice_id: str