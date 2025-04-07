from pydantic import BaseModel


class ChannelBulkMessageSchema(BaseModel):
    head_hunter: bool
    whatsapp: bool
    session_id: str


class SendWhatsMessageSchema(BaseModel):
    whatsapp_numbers: str
    message: str