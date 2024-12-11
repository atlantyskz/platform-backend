from typing import Optional
from pydantic import BaseModel, Field

class CreateOrganizationRequest(BaseModel):

    name:str = Field(...)
    registered_address:str = Field(...)
    contact_information:str = Field(...)

class UpdateOrganizationRequest(BaseModel):
    name:Optional[str] = Field(None)
    registered_address:Optional[str] = Field(None)
    contact_information:Optional[str] = Field(None)
