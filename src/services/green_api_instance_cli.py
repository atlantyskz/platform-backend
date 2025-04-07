import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()


class GreenApiInstanceCli:
    def __init__(self):
        self.__api_url = os.getenv("GREEN_API_URL")

    async def send_message(self, data: dict, instance_id: str, instance_token: str) -> dict:
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

    async def send_buttons_message(self, data: dict, instance_id: str, instance_token: str) -> dict:
        url = f"{self.__api_url}/waInstance{instance_id}/sendButtons/{instance_token}"
        print(url)
        payload = {
            "chatId": data["chat_id"],
            "message": data["message"],
            "footer": data.get("footer", ""),
            "buttons": data["buttons"]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                ) as response:
                    response_data = await response.json()
                    print(f"Green API sendButtons response to {data['chat_id']}: {response_data}")
                    response.raise_for_status()
                    return response_data
        except Exception as e:
            print(f"Error sending buttons to {data['chat_id']}: {str(e)}")
            return {"success": False, "error": str(e)}
