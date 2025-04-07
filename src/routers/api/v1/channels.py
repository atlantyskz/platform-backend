from fastapi import APIRouter, Depends

from src.core.middlewares.auth_middleware import get_current_user
from src.core.tasks import bulk_send_whatsapp_message
from src.schemas.responses.channels import ChannelBulkMessageSchema

router = APIRouter(prefix="/api/v1/channels", tags=["CHANNELS"])


@router.post("/bulk-message")
async def bulk_message(
        data: ChannelBulkMessageSchema,
        current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    bulk_send_whatsapp_message.delay(data.session_id, user_id)
    return {"success": True}
