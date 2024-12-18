from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class CreateOrganizationRequest(BaseModel):

    name:str = Field(...)
    email:EmailStr = Field(...)
    phone_number: Optional[str]
    registered_address:str = Field(...)

class UpdateOrganizationRequest(BaseModel):
    name:Optional[str] = Field(None)
    email:Optional[str] = Field(None)
    registered_address:Optional[str] = Field(None)
    phone_number:Optional[str] = Field(None)
