import aiohttp

from src.core.exceptions import BadRequestException


class HeadHunterCLI:
    async def send_hh_message(self, nid, message, api_token):
        url = f"https://api.hh.kz/negotiations/{nid}/messages"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"message": message}, headers={
                    "HH-User-Agent": "Atlantys 1.0 / (main@atlantys.kz)",
                    "Authorization": f"Bearer {api_token}"
                }) as response:
                    data = await response.json()
                    return data
        except aiohttp.ClientResponseError as e:
            raise BadRequestException("Error while sending message to vacancy") from e
        except aiohttp.ClientError as e:
            raise BadRequestException("Error while sending message to vacancy") from e
        except Exception as e:
            raise e

    async def get_vacancy_applicants(self, vacancy_id, page, per_page, api_token):
        url = f"https://api.hh.ru/negotiations/response?vacancy_id={vacancy_id}?page={page}&per_page={per_page}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={
                    "HH-User-Agent": "Atlantys 1.0 / (main@atlantys.kz)",
                    "Authorization": f"Bearer {api_token}"
                }) as response:
                    data = await response.json()
                    return data
        except aiohttp.ClientResponseError as e:
            raise BadRequestException("Error while getting vacancy applicants") from e
        except aiohttp.ClientError as e:
            raise BadRequestException("Error while getting vacancy applicants") from e
        except Exception as e:
            raise e
