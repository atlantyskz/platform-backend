from pydantic import BaseModel



class TopUpBillingRequest(BaseModel):
    atl_amount: float
    access_token: str
    invoice_id: str
