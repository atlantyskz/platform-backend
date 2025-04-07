from fastapi import APIRouter, Depends

from src import repositories
from src.core.databases import session_manager
from src.core.middlewares.auth_middleware import get_current_user
from src.core.tasks import bulk_send_whatsapp_message
from src.schemas.responses.channels import ChannelBulkMessageSchema, SendWhatsMessageSchema
from src.services.green_api_instance_cli import GreenApiInstanceCli

router = APIRouter(prefix="/api/v1/channels", tags=["CHANNELS"])


@router.post("/bulk-message")
async def bulk_message(
        data: ChannelBulkMessageSchema,
        current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")
    bulk_send_whatsapp_message.delay(data.session_id, user_id)
    return {"success": True}

@router.post("/send-whatsapp-message")
async def send_whatsapp_message(
    data: SendWhatsMessageSchema,
    current_user=Depends(get_current_user)
):
    user_id = current_user.get("sub")

    async with session_manager.session() as session:
        instance_repo = repositories.WhatsappInstanceRepository(session)
        current_instance_repo = repositories.CurrentWhatsappInstanceRepository(session)
        green_api_client = GreenApiInstanceCli()

        current_instance_id = await current_instance_repo.get_current_instance_id(user_id)
        if not current_instance_id:
            return {"success": False, "error": "Current WhatsApp instance not set"}

        whatsapp_instance = await instance_repo.get_by_id(current_instance_id)
        if not whatsapp_instance:
            return {"success": False, "error": "WhatsApp instance not found"}

        raw_numbers = [num.strip() for num in data.whatsapp_numbers.split(",") if num.strip()]

        sent = []
        failed = []

        for phone_number in raw_numbers:
            cleaned_number = "".join([c for c in phone_number if c.isdigit()])
            if cleaned_number.startswith("8"):
                cleaned_number = "7" + cleaned_number[1:]
            chat_id = f"{cleaned_number}@c.us"

            response = await green_api_client.send_message(
                data={
                    "chat_id": chat_id,
                    "message": data.message
                },
                instance_id=whatsapp_instance.instance_id,
                instance_token=whatsapp_instance.instance_token
            )

            if response.get("idMessage"):
                sent.append(chat_id)
            else:
                failed.append({"chat_id": chat_id, "error": response.get("error", "unknown")})

        return {
            "success": True,
            "sent": sent,
            "failed": failed
        }
