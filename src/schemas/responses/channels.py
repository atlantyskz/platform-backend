from pydantic import BaseModel


class ChannelBulkMessageSchema(BaseModel):
    head_hunter: bool
    whatsapp: bool
    session_id: str
