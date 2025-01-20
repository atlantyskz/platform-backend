from pydantic import BaseModel

class AddAssistantRequest(BaseModel):
    assistant_id:int
    
class RenameRequest(BaseModel):
    new_title:str