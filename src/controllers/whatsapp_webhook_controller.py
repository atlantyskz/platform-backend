from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src import repositories
from src.services.green_api_instance_cli import GreenApiInstanceCli


class WhatsappWebhookController:
    def __init__(
            self,
            session: AsyncSession
    ):
        print("[INIT] WhatsappWebhookController: Инициализация контроллера")
        self.session = session
        self.user_interaction_repo = repositories.UserInteractionRepository(session)
        self.whatsapp_instance_repo = repositories.WhatsappInstanceRepository(session)
        self.green_api_instance_client = GreenApiInstanceCli()
        self.session_repository = repositories.AssistantSessionRepository(session)

    async def handle_incoming_webhook(self, data: dict) -> dict:
        webhook_type = data.get("typeWebhook")

        instance_id = str(data.get("instanceData", {}).get("idInstance"))
        instance_wid = data.get("instanceData", {}).get("wid")
        sender_chat_id = data.get("senderData", {}).get("chatId")
        whatsapp_instance = await self.whatsapp_instance_repo.get_by_instance_id(instance_id)

        sender = await self.user_interaction_repo.get_interaction_by_chat_id(sender_chat_id, whatsapp_instance.id)
        print(sender)
        if not sender:
            return {}

        if webhook_type == "incomingMessageReceived":
            print(data)
            return await self._handle_incoming_message(data, whatsapp_instance)

        if webhook_type == "pollAnswer":
            return await self._handle_poll_answer(data, whatsapp_instance)

        return {"status": "ignored"}

    async def _handle_incoming_message(self, data: dict, instance) -> dict:
        chat_id = data["senderData"].get("chatId")
        message_text = data.get("messageData", {}).get("textMessageData", {}).get("textMessage", "")

        if not chat_id or not message_text:
            return {"status": "no_chat_id_or_text"}

        interaction = await self.user_interaction_repo.get_not_answered_by_chat(
            chat_id,
            instance.id,
            "RESUME_OFFER"
        )
        if not interaction:
            return {"status": "no_interaction"}
        print(interaction)
        if interaction.is_answered:
            return {"status": "already_answered"}

        if interaction.created_at + timedelta(hours=24) < datetime.utcnow():
            print("HELLLLLOOOOO")
            return {"status": "time expired"}

        user_answer = message_text.strip()

        if user_answer == "1":
            reply = (
                "Отлично! Давайте обсудим детали онлайн. "
                "Пожалуйста выберите удобное вам время для звонка "
                "https://calendly.com/main-atlantys/30min"
            )
            await self.user_interaction_repo.mark_answered(interaction.id, True)

        elif user_answer == "2":
            reply = (
                "Спасибо за честный ответ. Если в будущем захотите продолжить общение, "
                "мы будем рады с вами связаться."
            )
            await self.user_interaction_repo.mark_answered(interaction.id, False)

        else:
            reply = "Пожалуйста, отправьте «1» или «2», чтобы выбрать один из вариантов."
        if instance:
            await self.green_api_instance_client.send_message(
                data={"chat_id": chat_id, "message": reply},
                instance_id=instance.instance_id,
                instance_token=instance.instance_token
            )

        await self.session.commit()
        return {"status": "message_received", "reply": reply}

    async def _handle_poll_answer(self, data: dict, instance) -> dict:
        return {"status": "poll_answer_handled"}
