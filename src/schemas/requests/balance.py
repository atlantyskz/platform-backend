from pydantic import BaseModel

class TopupBalanceRequest(BaseModel):
    amount: int

