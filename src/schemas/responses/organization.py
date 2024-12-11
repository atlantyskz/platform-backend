from pydantic import BaseModel, Field

class CreateOrganizationResponse(BaseModel):

    name:str = Field(...)
    admin_firstname:str
    admin_lastname:str