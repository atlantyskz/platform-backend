import asyncio
import logging
from typing import List
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import retries
from dramatiq.middleware import time_limit
from dramatiq.middleware.asyncio import AsyncIO
from dramatiq.brokers.redis import RedisBroker

redis_broker = RedisBroker(host="redis", port=6379)

redis_broker.add_middleware(AsyncIO())  
redis_broker.add_middleware(retries.Retries())    
redis_broker.add_middleware(time_limit.TimeLimit())

dramatiq.set_broker(redis_broker)
@dramatiq.actor
async def process_resumes_batch(task_ids: List[str], vacancy_text: str, resumes_texts: List[str]):
    from src.core.backend import BackgroundTasksBackend
    from src.services.request_sender import RequestSender
    from src.core.databases import session_manager

    postgres = session_manager

    async with postgres.session() as session:
        try:
            bg_session = BackgroundTasksBackend(session)
            llm_service = RequestSender()

            tasks = [
                llm_service._send_request({
                    'vacancy_text': vacancy_text,
                    'cv_text': resume_text
                }) for resume_text in resumes_texts
            ]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for task_id, response in zip(task_ids, responses):
                if isinstance(response, Exception):
                    await bg_session.update_task_result(
                        task_id=task_id,
                        result_data={"error": str(response)},
                        tokens_spent={"error": str(response)},
                        status="failed"
                    )
                else:
                    await bg_session.update_task_result(
                        task_id=task_id,
                        result_data=response.get('llm_response'),
                        tokens_spent=response.get('tokens_spent'),
                        status="completed"
                    )

        except Exception as e:
            logging.error(f'Connection failed - {str(e)}')
            for task_id in task_ids:
                await bg_session.update_task_result(
                    task_id=task_id,
                    result_data={"error": str(e)},
                    tokens_spent={"error": str(e)},
                    status="failed"
                )
