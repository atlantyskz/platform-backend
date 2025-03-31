from pydantic import BaseModel, constr


class BankCardCreate(BaseModel):
    card_number: constr(min_length=16, max_length=16)


class BankCardResponse(BaseModel):
    id: int
    card_number: str

    class Config:
        from_attributes = True
