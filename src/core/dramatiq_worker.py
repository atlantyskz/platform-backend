import logging

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import time_limit
from dramatiq.middleware.asyncio import AsyncIO

from src.repositories.balance import BalanceRepository
from src.repositories.balance_usage import BalanceUsageRepository

redis_broker = RedisBroker(host="redis", port=6379)
redis_broker.add_middleware(AsyncIO())
redis_broker.add_middleware(time_limit.TimeLimit())
dramatiq.set_broker(redis_broker)


class DramatiqWorker:

    @staticmethod
    @dramatiq.actor(max_retries=3, min_backoff=1000)
    async def process_resume(
            task_id: str,
            vacancy_text: str,
            resume_text: str,
            user_id: int,
            organization_id: int,
            balance_id: int,
            user_message: str,
            file=None
    ):
        from src.core.backend import BackgroundTasksBackend
        from src.repositories.assistant import AssistantRepository
        from src.services.request_sender import RequestSender
        from src.core.databases import session_manager

        logging.info(f"Начало задачи {task_id} для user_id={user_id}")

        try:
            async with session_manager.session() as session:
                async with session.begin():
                    bg_session = BackgroundTasksBackend(session)
                    balance_repo = BalanceRepository(session)
                    assistant_repo = AssistantRepository(session)
                    usage_repo = BalanceUsageRepository(session)
                    llm_service = RequestSender()

                    balance = await balance_repo.get_balance(organization_id)
                    if balance.atl_tokens < 5:
                        raise ValueError(f"Недостаточно ATL токенов: {balance.atl_tokens} < 5")

                    prompt = [{"role": "user", "content": f"vacancy_text:{vacancy_text} resume_text:{resume_text}"}]
                    response_data = await llm_service._send_request(data={'messages': prompt})

                    if not response_data or "llm_response" not in response_data or response_data.get("error"):
                        raise ValueError("Некорректный ответ от LLM")

                    llm_tokens = response_data.get("tokens_spent", 0)
                    atl_tokens = round(llm_tokens / 3000, 2)

                    assistant = await assistant_repo.get_assistant_by_name("ИИ Рекрутер")

                    await usage_repo.create({
                        'user_id': user_id,
                        'assistant_id': assistant.id,
                        'type': "resume analysis",
                        'organization_id': organization_id,
                        'balance_id': balance_id,
                        'input_text_count': len(user_message),
                        'gpt_token_spent': llm_tokens,
                        'input_token_count': llm_tokens,
                        'file_count': 1 if file else 0,
                        'file_size': getattr(file, 'size', None),
                        'atl_token_spent': atl_tokens,
                    })

                    if not await balance_repo.withdraw_balance(organization_id, atl_tokens):
                        raise ValueError("Не удалось списать ATL токены — возможно, недостаточно средств")

                    await bg_session.update_task_result(
                        task_id=task_id,
                        result_data=response_data["llm_response"],
                        tokens_spent=llm_tokens,
                        status="completed"
                    )
                    logging.info(f"Задача {task_id} завершена успешно")

        except Exception as e:
            logging.error(f"Ошибка в задаче {task_id}: {e}")
            async with session_manager.session() as session:
                bg_session = BackgroundTasksBackend(session)
                await bg_session.update_task_result(
                    task_id=task_id,
                    result_data={"error": str(e)},
                    tokens_spent=0,
                    status="failed"
                )
            raise
