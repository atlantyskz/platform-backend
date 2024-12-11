from typing import Optional
from pydantic import BaseModel, Field,EmailStr

class CreateOrganizationMemberRequest(BaseModel):

    firstname:str = Field(...)
    lastname:str = Field(...)
    email:EmailStr = Field(...)
    password:str = Field(...)
    role_alias:str = Field(...)

class UpdateOrganizationMemberRequest(BaseModel):
    employee_id:Optional[int] = Field(None)
    firstname:Optional[str] = Field(None)
    lastname:Optional[str] = Field(None)
    email:Optional[EmailStr] = Field(None)
    password:Optional[str] = Field(None)
    role_alias:Optional[str] = Field(None)
