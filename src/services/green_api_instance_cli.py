import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()


class GreenApiInstanceCli:
    def __init__(self):
        self.__api_url = os.getenv("GREEN_API_URL")

    async def send_message(self, data: dict, instance_id: str, instance_token: str) -> dict:
        """
        Отправка обычного текстового сообщения в WhatsApp.

        :param data: словарь с ключами:
            - "chat_id" (str) -> номер WhatsApp в формате '79991112233@c.us'
            - "message" (str) -> текст сообщения
        :param instance_id: идентификатор инстанса, возвращённый при создании
        :param instance_token: API-токен инстанса, возвращённый при создании
        :return: JSON-ответ (dict) с результатом отправки
        """
        url = f"{self.__api_url}/waInstance{instance_id}/sendMessage/{instance_token}"
        chat_id = data.get("chat_id")
        message = data.get("message")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        json={"chatId": chat_id, "message": message},
                        headers={"Content-Type": "application/json"}
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_poll(self, data: dict, instance_id: str, instance_token: str) -> dict:
        """
        Отправка опроса (Poll) в WhatsApp.
        Обратите внимание, что метод 'sendPoll' может быть экспериментальным
        или кастомным эндпоинтом Green API; перепроверьте документацию.

        :param data: словарь с ключами:
            - "chat_id" (str) -> номер WhatsApp в формате '79991112233@c.us'
            - "message" (str) -> текст / вопрос опроса
            - "options" (list[str]) -> список вариантов ответа
        :param instance_id: идентификатор инстанса
        :param instance_token: API-токен инстанса
        :return: JSON-ответ (dict) с результатом отправки
        """
        url = f"{self.__api_url}/waInstance{instance_id}/sendPoll/{instance_token}"
        chat_id = data.get("chat_id")
        message = data.get("message")
        options = data.get("options")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        json={
                            "chatId": chat_id,
                            "message": message,
                            "options": options
                        },
                        headers={"Content-Type": "application/json"}
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_poll_answer(self, instance_id: str, instance_token: str, message_id: str) -> dict:
        """
        Получение ответа на отправленный опрос (Poll).
        Предполагается, что метод 'getPollAnswer' доступен в Green API.
        Убедитесь, что message_id соответствует id сообщения с опросом.

        :param instance_id: идентификатор инстанса
        :param instance_token: API-токен инстанса
        :param message_id: идентификатор сообщения с опросом
        :return: JSON-ответ (dict) с данными об ответах на опрос
        """
        url = f"{self.__api_url}/waInstance{instance_id}/getPollAnswer/{instance_token}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        json={"idMessage": message_id},
                        headers={"Content-Type": "application/json"}
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
