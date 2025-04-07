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

    async def handle_incoming_webhook(self, data: dict) -> dict:
        webhook_type = data.get("typeWebhook")
        instance_id = data.get("instanceData", {}).get("idInstance")
        instance_wid = data.get("instanceData", {}).get("wid")
        sender_chat_id = data.get("senderData", {}).get("chatId")

        whatsapp_instance = await self.whatsapp_instance_repo.get_by_instance_id(instance_id)

        if webhook_type == "pollAnswer":
            return await self._handle_poll_answer(data, whatsapp_instance)

        if webhook_type == "incomingMessageReceived":
            return {"status": "text_message_ignored"}

        return {"status": "ignored"}

    async def _handle_poll_answer(self, data: dict, instance) -> dict:
        chat_id = data["senderData"].get("chatId")
        answer = data["messageData"].get("optionAnswer")
        message_id = data["messageData"].get("idMessage")

        if not chat_id or not answer:
            return {"error": "Invalid poll answer data"}

        interaction = await self.user_interaction_repo.get_not_answered_by_chat(
            chat_id, "RESUME_OFFER"
        )
        if interaction:
            await self.user_interaction_repo.mark_answered(interaction.id, answer)

        reply = None
        if answer == "Продолжить":
            reply = "Отлично! Давайте обсудим детали. Расскажите немного о себе."
        elif answer == "Не интересует":
            reply = "Спасибо за честный ответ. Если что — будем на связи."

        if reply:
            if instance:
                await self.green_api_instance_client.send_message(
                    data={"chat_id": chat_id, "message": reply},
                    instance_id=instance.instance_id,
                    instance_token=instance.instance_token
                )

        return {"status": f"poll_answer_received: {answer}"}
