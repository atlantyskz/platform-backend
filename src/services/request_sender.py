import logging
import httpx
from abc import ABC, abstractmethod
import json as json_converter

logging.basicConfig(level=logging.INFO)

class IRequestSender(ABC):
    @abstractmethod
    async def _send_request(self, llm_url: str, data: dict) -> dict:
        pass

class RequestSender(IRequestSender):

    LLM_URL = 'http://0.0.0.0:8001/hr/analyze_cv_by_vacancy'

    async def _send_request(self, data: dict ,llm_url: str = LLM_URL) -> dict:
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(llm_url, json=data,headers=headers)
                response_data = response.json()
                logging.info(response_data)
                return response_data
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise Exception(f"HTTP error occurred: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            raise Exception(f"Unexpected error occurred: {e}")
