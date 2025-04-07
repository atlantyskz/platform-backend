import json
import os

import aiohttp
from dotenv import load_dotenv
from websockets import connect

load_dotenv()


class GreenApiCli:
    def __init__(self):
        self.__partner_url = os.getenv("GREEN_API_PARTNER_URL")
        self.__partner_token = os.getenv("GREEN_API_PARTNER_TOKEN")
        self.__webhook_url = os.getenv("GREEN_API_WEBHOOK")
        self.__webhook_token = os.getenv("GREEN_API_WEBHOOK_TOKEN")
        self.__api_url = os.getenv("GREEN_API_URL")

    async def create_instance(self, data: dict) -> dict:
        url = f"{self.__partner_url}/partner/createInstance/{self.__partner_token}"
        print(url)
        payload = {
            "name": data.get("email"),
            "webhookUrl": self.__webhook_url,
            "webhookUrlToken": self.__webhook_token,
            "outgoingAPIMessageWebhook": "yes",
            "outgoingWebhook": "yes",
            "outgoingMessageWebhook": "yes",
            "incomingWebhook": "yes",
            "deviceWebhook": "no",
            "stateWebhook": "no",
            "keepOnlineStatus": "no",
            "pollMessageWebhook": "yes",
            "incomingBlockWebhook": "yes",
            "incomingCallWebhook": "no",
            "editedMessageWebhook": "no",
            "deletedMessageWebhook": "no",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 401:
                        return {
                            "success": False,
                            "error": "Unauthorized (401)",
                        }
                    response.raise_for_status()

                    resp_data = await response.json()

                    if "Unauthorized" in str(resp_data):
                        return {
                            "success": False,
                            "error": "Unauthorized",
                        }

                    return {
                        "success": True,
                        "instance_id": resp_data.get("idInstance"),
                        "instance_token": resp_data.get("apiTokenInstance"),
                        "instance_type": resp_data.get("typeInstance"),
                        "data": resp_data,
                    }

        except aiohttp.ClientResponseError as e:
            return {
                "success": False,
                "error": f"HTTP Error: {e.status} {e.message}"
            }
        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"Client Error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected Error: {str(e)}"
            }

    async def get_instance_state(self, instance_id: str, instance_token: str) -> dict:
        url = f"{self.__api_url}/waInstance{instance_id}/getStateInstance/{instance_token}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={}) as response:
                    response.raise_for_status()
                    resp_data = await response.json()
                    return {
                        "success": True,
                        "state_instance": resp_data.get("stateInstance"),
                    }
        except aiohttp.ClientResponseError as e:
            return {
                "success": False,
                "error": f"HTTP Error: {e.status} {e.message}"
            }
        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"Client Error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected Error: {str(e)}"
            }

    async def get_qr_code(self, instance_id: str, instance_token: str) -> dict:
        url = f"{self.__api_url}/waInstance{instance_id}/qr/{instance_token}"
        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if data.get("type") == "qrCode":
                        return {
                            "success": True,
                            "message": data.get("message"),
                            "type": data.get("type"),
                        }

                    return {
                        "success": False,
                        "error": f"Unexpected response: {data}"
                    }

        except aiohttp.ClientResponseError as http_err:
            return {"success": False, "error": f"HTTP error: {str(http_err)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    async def reboot_instance(self, instance_id: str, instance_token: str) -> dict:
        url = f"{self.__api_url}/waInstance{instance_id}/reboot/{instance_token}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return {
                        "success": True,
                        "data": data
                    }
        except aiohttp.ClientResponseError as e:
            return {
                "success": False,
                "error": f"HTTP Error: {e.status} {e.message}"
            }
        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"Client Error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected Error: {str(e)}"
            }
