import logging
import httpx
from typing import Any, Dict
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)

class IRequestSender(ABC):
    @abstractmethod
    async def _send_request(self, llm_url: str, data: dict) -> dict:
        pass

class RequestSender(IRequestSender):

    LLM_URL = "http://llm_service:8001/hr/analyze_cv_by_vacancy"

    async def _send_request(self, data: Dict[str, Any], llm_url: str = LLM_URL) -> Dict[str, Any]:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, read=120.0)) as client:
                response = await client.post(llm_url, json=data, headers=headers)
                response.raise_for_status()  
                response_data = response.json()
                logging.info("Response data: %s", response_data)
                return response_data
        except httpx.HTTPStatusError as http_err:
            logging.error(f"HTTP error occurred: {http_err.response.status_code} - {http_err.response.text}")
            raise Exception(f"HTTP error: {http_err.response.status_code} - {http_err.response.text}") from http_err
        except httpx.RequestError as req_err:
            logging.error(f"Request error occurred: {req_err}")
            raise Exception(f"Request error: {req_err}") from req_err
        except Exception as err:
            logging.error(f"Unexpected error occurred: {err}")
            raise Exception(f"Unexpected error: {err}") from err