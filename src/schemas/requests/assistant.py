from pydantic import BaseModel

class AddAssistantRequest(BaseModel):
    assistant_id:int
    