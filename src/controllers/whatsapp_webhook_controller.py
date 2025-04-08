from sqlalchemy.ext.asyncio import AsyncSession

from src import repositories
from src.services.green_api_instance_cli import GreenApiInstanceCli


class WhatsappWebhookController:
    def __init__(
        self,
        session: AsyncSession
    ):
        print("[INIT] WhatsappWebhookController: Инициализация контроллера")
        self.user_interaction_repo = repositories.UserInteractionRepository(session)
        self.whatsapp_instance_repo = repositories.WhatsappInstanceRepository(session)
        self.green_api_instance_client = GreenApiInstanceCli()
        print("[INIT] Репозитории и GreenApiInstanceCli инициализированы")

    async def handle_incoming_webhook(self, data: dict) -> dict:
        """
        Функция обрабатывает входящий вебхук от WhatsApp (Green API).
        В зависимости от типа события (webhook_type), мы либо разбираем опрос,
        либо анализируем входящее сообщение.
        """

        print("[handle_incoming_webhook] Получены данные вебхука:", data)
        # Тип события, например "incomingMessageReceived"
        webhook_type = data.get("typeWebhook")

        instance_id = data.get("instanceData", {}).get("idInstance")
        instance_wid = data.get("instanceData", {}).get("wid")
        sender_chat_id = data.get("senderData", {}).get("chatId")

        print("[handle_incoming_webhook] webhook_type:", webhook_type)
        print("[handle_incoming_webhook] instance_id:", instance_id)
        print("[handle_incoming_webhook] instance_wid:", instance_wid)
        print("[handle_incoming_webhook] sender_chat_id:", sender_chat_id)

        whatsapp_instance = await self.whatsapp_instance_repo.get_by_instance_id(str(instance_id))
        print("[handle_incoming_webhook] WhatsApp Instance:", whatsapp_instance)

        if webhook_type == "incomingMessageReceived":
            print("[handle_incoming_webhook] Обнаружено входящее сообщение, обрабатываем")
            return await self._handle_incoming_message(data, whatsapp_instance)

        if webhook_type == "pollAnswer":
            print("[handle_incoming_webhook] Обнаружен pollAnswer")
            return await self._handle_poll_answer(data, whatsapp_instance)

        print("[handle_incoming_webhook] Другой тип вебхука, игнорируем")
        return {"status": "ignored"}

    async def _handle_incoming_message(self, data: dict, instance) -> dict:
        """
        Обрабатывает обычное текстовое сообщение (incomingMessageReceived).
        Предполагается, что пользователь может отправить '1', '2' или что-то другое.
        """
        print("[_handle_incoming_message] Старт обработки входящего сообщения:", data)

        chat_id = data["senderData"].get("chatId")
        message_text = data.get("messageData", {}).get("textMessageData", {}).get("textMessage", "")
        print("[_handle_incoming_message] chat_id:", chat_id)
        print("[_handle_incoming_message] message_text:", message_text)

        if not chat_id or not message_text:
            print("[_handle_incoming_message] Нет chat_id или пустое сообщение — выходим.")
            return {"status": "no_chat_id_or_text"}

        interaction = await self.user_interaction_repo.get_not_answered_by_chat(
            chat_id,
            "RESUME_OFFER"
        )
        print("[_handle_incoming_message] Найдено взаимодействие:", interaction)

        if not interaction:
            print("[_handle_incoming_message] Нет незавершённого взаимодействия — игнорируем.")
            return {"status": "no_interaction"}

        user_answer = message_text.strip()
        if user_answer == "1":
            reply = (
                "Отлично! Давайте обсудим детали. "
                "Расскажите немного о себе, чтобы мы могли двигаться дальше."
            )
            await self.user_interaction_repo.mark_answered(interaction.id, "1")

        elif user_answer == "2":
            reply = (
                "Спасибо за честный ответ. Если в будущем захотите продолжить общение, "
                "мы будем рады с вами связаться."
            )
            await self.user_interaction_repo.mark_answered(interaction.id, "2")

        else:
            reply = "Пожалуйста, отправьте «1» или «2», чтобы выбрать один из вариантов."

        print("[_handle_incoming_message] Итоговый ответ боту:", reply)

        if instance:
            print("[_handle_incoming_message] Отправляем сообщение через Green API")
            await self.green_api_instance_client.send_message(
                data={"chat_id": chat_id, "message": reply},
                instance_id=instance.instance_id,
                instance_token=instance.instance_token
            )

        return {"status": "message_received", "reply": reply}

    async def _handle_poll_answer(self, data: dict, instance) -> dict:
        """
        Если у вас осталась логика по обработке "pollAnswer" — можно оставить как было.
        Но если опросов нет, просто уберите этот метод.
        """
        print("[_handle_poll_answer] Обработка ответа на опрос. Исходные данные:", data)
        # ...
        return {"status": "poll_answer_handled"}
