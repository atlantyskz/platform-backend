from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from typing_extensions import Annotated
class CreateOrganizationRequest(BaseModel):

    name:Annotated[str,Field(strict=True)]
    email:EmailStr = Field(...)
    phone_number: Optional[str]
    registered_address:str = Field(...)

class UpdateOrganizationRequest(BaseModel):
    name:Optional[str] = Field(None)
    email:Optional[str] = Field(None)
    registered_address:Optional[str] = Field(None)
    phone_number:Optional[str] = Field(None)
