import json
import logging
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import retries
from dramatiq.middleware import time_limit
from dramatiq.middleware.asyncio import AsyncIO
from dramatiq_abort import Abort
from dramatiq_abort import Abortable, backends
from sqlalchemy import select, text

from src.repositories.balance import BalanceRepository
from src.repositories.balance_usage import BalanceUsageRepository


redis_broker = RedisBroker(host="redis", port=6379)
event_backend = backends.RedisBackend()
abortable = Abortable(backend=event_backend)
redis_broker.add_middleware(abortable)
redis_broker.add_middleware(AsyncIO())  
redis_broker.add_middleware(time_limit.TimeLimit())
class DramatiqWorker:
    @dramatiq.actor(abortable=True, max_retries=0)  # Отключаем ретраи
    async def process_resume(task_id: str, vacancy_text: str, resume_text: str, user_id: int, 
                            organization_id: int, balance_id: int, user_message: str, file=None):
        from src.core.backend import BackgroundTasksBackend
        from src.services.request_sender import RequestSender
        from src.core.databases import session_manager
        
        postgres = session_manager
        async with postgres.session() as session:
            async with session.begin():
                    bg_session = BackgroundTasksBackend(session)
                    balance_repo = BalanceRepository(session)
                    
                    # Блокируем баланс для чтения
                    await session.execute(
                        text("SELECT * FROM balances WHERE organization_id = :org_id FOR UPDATE"),
                        {"org_id": organization_id}
                    )
                    
                    balance = await balance_repo.get_balance(organization_id)
                    if balance.atl_tokens < 5:
                        # Обновляем статус и выходим без исключения
                        await bg_session.update_task_result(
                            task_id=task_id,
                            result_data={"error": "Insufficient balance - minimum 5 tokens required"},
                            tokens_spent=0,
                            status="rejected"
                        )
                        await session.commit()
                        return  # ВАЖНО: ВЫХОД ИЗ ФУНКЦИИ, ЧТОБЫ НЕ БЫЛО RETRY

                    # Создаём новую транзакцию
                    async with session.begin():
                        llm_service = RequestSender()
                        messages = [{
                            "role": "user",
                            "content": f"vacancy_text:{vacancy_text} resume_text:{resume_text}"
                        }]
                        
                        try:
                            response = await llm_service._send_request(data={'messages': messages})
                        except Exception as e:
                            await bg_session.update_task_result(
                                task_id=task_id,
                                result_data={"error": f"LLM service error: {str(e)}"},
                                tokens_spent=0,
                                status="failed"
                            )
                            raise

                        llm_tokens = response.get('tokens_spent')
                        atl_tokens_spent = round(llm_tokens / 3000, 2)
                        
                        # Списываем баланс
                        withdraw_result = await balance_repo.withdraw_balance(organization_id, atl_tokens_spent)
                        if not withdraw_result:
                            await bg_session.update_task_result(
                                task_id=task_id,
                                result_data={"error": "Failed to withdraw balance"},
                                tokens_spent=0,
                                status="failed"
                            )
                            return  # ВЫХОД БЕЗ RETRY

                        # Создаём запись использования
                        balance_usage_repo = BalanceUsageRepository(session)
                        usage_data = {
                            'user_id': user_id,
                            'organization_id': organization_id,
                            'balance_id': balance_id,
                            'input_text_count': len(user_message),
                            'gpt_token_spent': llm_tokens,
                            'input_token_count': llm_tokens,
                            'file_count': 1 if file else 0,
                            'file_size': file.size if file else None,
                            'atl_token_spent': atl_tokens_spent
                        }
                        
                        await balance_usage_repo.create(usage_data)
                        
                        # Обновляем результат задачи
                        await bg_session.update_task_result(
                            task_id=task_id,
                            result_data=response.get('llm_response'),
                            tokens_spent=llm_tokens,
                            status="completed"
                        )
                        
                        await session.commit()
