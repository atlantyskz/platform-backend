import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src import repositories
from src.services.green_api_instance_cli import GreenApiInstanceCli

logger = logging.getLogger(__name__)


class WhatsappWebhookController:
    def __init__(
            self,
            session: AsyncSession
    ):
        self.user_interaction_repo = repositories.UserInteractionRepository(session)
        self.whatsapp_instance_repo = repositories.WhatsappInstanceRepository(session)
        self.green_api_instance_client = GreenApiInstanceCli()

    async def handle_incoming_webhook(self, data: dict, instance_id) -> dict:
        if not data:
            return {"error": "No data provided"}

        if data.get("typeWebhook") == "incomingMessageReceived":
            return await self._handle_incoming_message(data, instance_id)

        return {"status": "ignored"}

    async def _handle_incoming_message(self, data: dict, instance_id) -> dict:
        message_data = data.get("messageData", {})
        message_type = message_data.get("typeMessage")

        if message_type == "buttonMessage":
            return await self._handle_button_message(data)

        if message_type == "textMessage":
            sender = data.get("senderData", {}).get("sender")
            text_message = message_data.get("textMessageData", {}).get("textMessage")
            logger.info(f"Текстовое сообщение от {sender}: {text_message}")
            return {"status": "text_received"}

        return {"status": "unhandled_message_type"}

    async def _handle_button_message(self, data: dict, instance_id) -> dict:
        button_id = data["messageData"]["buttonMessageData"]["buttonId"]
        chat_id = data["senderData"].get("chatId")  # например "79001234567@c.us"

        interaction = await self.user_interaction_repo.get_not_answered_by_chat(
            chat_id, "RESUME_OFFER"
        )
        if not interaction:
            logger.info("No active interaction found for chat_id=%s", chat_id)
            return {"status": "interaction_not_found"}

        await self.user_interaction_repo.mark_answered(interaction.id, button_id)
        reply_text = None
        if button_id == "continue":
            reply_text = "Отлично! Давайте обсудим детали. Можете рассказать о своём опыте..."
        elif button_id == "not_interested":
            reply_text = "Спасибо за ответ. Если что, будем на связи!"

        if reply_text:
            instance = await self.whatsapp_instance_repo.get_by_instance_id(instance_id)
            if instance:
                data_send = {"chat_id": chat_id, "message": reply_text}
                await self.green_api_instance_client.send_message(
                    data_send,
                    instance_id=instance.instance_id,
                    instance_token=instance.instance_token
                )
            else:
                logger.warning("Не найден активный инстанс для отправки ответа")

        return {"status": f"button_{button_id}_received"}
