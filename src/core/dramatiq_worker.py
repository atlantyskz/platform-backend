import json
import logging
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import retries
from dramatiq.middleware import time_limit
from dramatiq.middleware.asyncio import AsyncIO
from dramatiq.brokers.redis import RedisBroker

from src.repositories.balance import BalanceRepository
from src.repositories.balance_usage import BalanceUsageRepository


redis_broker = RedisBroker(host="redis", port=6379)

redis_broker.add_middleware(AsyncIO())  
redis_broker.add_middleware(retries.Retries())    
redis_broker.add_middleware(time_limit.TimeLimit())

dramatiq.set_broker(redis_broker)

class DramatiqWorker:
    @dramatiq.actor
    async def process_resume(task_id: str, vacancy_text: str, resume_text: str, user_id: int, 
                              organization_id: int, balance_id: int, user_message: str, file=None):
        logging.info(f"Начало обработки задачи task_id={task_id} для user_id={user_id}")
        from src.core.backend import BackgroundTasksBackend
        from src.repositories.assistant import AssistantRepository
        from src.services.request_sender import RequestSender
        from src.core.databases import session_manager
        
        postgres = session_manager
        async with postgres.session() as session:
            # Начало транзакции
            async with session.begin():
                try:
                    logging.debug("Инициализация репозиториев и сервисов")
                    bg_session = BackgroundTasksBackend(session)
                    balance_usage_repo = BalanceUsageRepository(session)
                    assistant_repo = AssistantRepository(session)
                    balance_repo = BalanceRepository(session)
                    
                    logging.info(f"Получение баланса для организации {organization_id}")
                    balance = await balance_repo.get_balance(organization_id)
                    logging.debug(f"Полученный баланс: {balance}")
                    if balance.atl_tokens < 5:
                        error_msg = f"Недостаточно средств: имеется {balance.atl_tokens} токенов, требуется минимум 5"
                        logging.error(error_msg)
                        raise ValueError(error_msg)
                    
                    llm_service = RequestSender()
                    messages = [{
                        "role": "user",
                        "content": f"vacancy_text:{vacancy_text} resume_text:{resume_text}"
                    }]
                    logging.info("Отправка запроса к LLM сервису")
                    response = await llm_service._send_request(data={'messages': messages})
                    logging.debug(f"Ответ от LLM сервиса: {response}")
                    llm_tokens = response.get('tokens_spent', 0)
                    atl_tokens_spent = round(llm_tokens / 3000, 2)
                    
                    assistant = await assistant_repo.get_assistant_by_name("ИИ Рекрутер")
                    logging.info(f"Получен ассистент: {assistant}")
                    logging.info(f"TOKENS SPENT: {atl_tokens_spent}")
                    
                    logging.info("Запись использования баланса")
                    await balance_usage_repo.create({
                        'user_id': user_id,
                        "assistant_id": assistant.id,
                        "type": "resume analysis",
                        'organization_id': organization_id,
                        'balance_id': balance_id,
                        'input_text_count': len(user_message),
                        'gpt_token_spent': llm_tokens,
                        'input_token_count': llm_tokens,
                        'file_count': 1 if file else 0,
                        'file_size': file.size if file else None,
                        'atl_token_spent': atl_tokens_spent
                    })
                    
                    logging.info(f"Снятие {atl_tokens_spent} токенов с баланса организации {organization_id}")
                    withdraw_result = await balance_repo.withdraw_balance(organization_id, atl_tokens_spent)
                    if not withdraw_result:
                        error_msg = "Не удалось списать средства с баланса: недостаточно средств или иная проблема"
                        logging.error(error_msg)
                        raise ValueError(error_msg)
                    
                    logging.info("Обновление результата задачи как 'completed'")
                    await bg_session.update_task_result(
                        task_id=task_id,
                        result_data=response.get('llm_response') if response else {"error": "Unknown error"},
                        tokens_spent=llm_tokens,
                        status="completed" if response else "failed"
                    )
                    logging.info(f"Задача {task_id} успешно завершена")

                except Exception as e:
                    logging.error(f"Задача {task_id} завершилась с ошибкой: {str(e)}")
                    await bg_session.update_task_result(
                        task_id=task_id,
                        result_data={"error": str(e)},
                        tokens_spent=0, 
                        status="failed"
                    )
                    raise  # Повторное возбуждение исключения для обеспечения отката транзакции