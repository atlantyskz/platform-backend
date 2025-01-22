import json
import logging
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
async def process_resume(task_id: str, vacancy_text: str, resume_text: str):
    from src.core.backend import BackgroundTasksBackend
    from src.services.request_sender import RequestSender
    from src.core.databases import session_manager

    postgres = session_manager
    
    async with postgres.session() as session:

        try:
            bg_session = BackgroundTasksBackend(session)
            llm_service = RequestSender()
            messages = [{
                "role": "user",
                "content": f"vacancy_text:{vacancy_text} resume_text:{resume_text}"
            }]
            response = await llm_service._send_request(data={'messages':messages})

            await bg_session.update_task_result(
                task_id=task_id,
                result_data=response.get('llm_response'),
                tokens_spent=response.get('tokens_spent'),
                status="completed", 
            )

        except Exception as e:
            print(f'Connection failed - {str(e)}')
            await bg_session.update_task_result(
                task_id=task_id,
                result_data={"error": str(e)},
                tokens_spent=0,
                status="failed"
            )