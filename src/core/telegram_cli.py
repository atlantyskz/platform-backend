import httpx


class TelegramCli:
    TELEGRAM_BOT_URL = "http://telegram-bot:9010/send_alert"  # Docker service name

    async def send_message(self, text: str, type_: str) -> None:
        """
        Sends a message to the Telegram bot API.

        :param text: The message text to send.
        :param type_: The type of the message, e.g., 'BUG' or 'FEATURE'.
        """
        type_ = type_.upper()

        if type_ == "BUG":
            message = f"🚨 *Ошибка сервера:* {text}"
        elif type_ == "FEATURE":
            message = f"✨ *Новый фичерек:* {text}"
        else:
            message = text

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.TELEGRAM_BOT_URL, json={"error_message": message})
        except httpx.RequestError as e:
            print(f"[TelegramCli] Failed to send message: {e}")
