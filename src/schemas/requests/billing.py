from pydantic import BaseModel



class TopUpBillingRequest(BaseModel):
    atl_amount: int
    access_token: str
    invoice_id: str
