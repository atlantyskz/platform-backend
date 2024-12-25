import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import retries
from dramatiq.middleware import time_limit
from dramatiq.middleware.asyncio import AsyncIO
from dramatiq.brokers.redis import RedisBroker

redis_broker = RedisBroker(host="redis", port=6379)

# Add necessary middleware
redis_broker.add_middleware(AsyncIO())  # Handles asyncio event loops
redis_broker.add_middleware(retries.Retries())    # Handles retries
redis_broker.add_middleware(time_limit.TimeLimit())  # Optional: sets execution time limit

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
            response = await llm_service._send_request({
                'vacancy_text':vacancy_text,
                'cv_text':resume_text
            })
            await bg_session.update_task_result(
                task_id=task_id,
                result_data=response,
                status="completed"
            )
        except Exception as e:
            print(f'Connection failed - {str(e)}')
            await bg_session.update_task_result(
                task_id=task_id,
                result_data={"error": str(e)},
                status="failed"
            )
