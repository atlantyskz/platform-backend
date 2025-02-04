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
        from src.core.backend import BackgroundTasksBackend
        from src.services.request_sender import RequestSender
        from src.core.databases import session_manager
        
        postgres = session_manager
        async with postgres.session() as session:
            # Start a transaction
            async with session.begin():
                try:
                    bg_session = BackgroundTasksBackend(session)
                    balance_usage_repo = BalanceUsageRepository(session)
                    balance_repo = BalanceRepository(session)
                    
                    balance = await balance_repo.get_balance(organization_id)
                    if balance.atl_tokens < 5:
                        raise ValueError("Insufficient balance")
                    
                    llm_service = RequestSender()
                    messages = [{
                        "role": "user",
                        "content": f"vacancy_text:{vacancy_text} resume_text:{resume_text}"
                    }]
                    
                    response = await llm_service._send_request(data={'messages': messages})
                    llm_tokens = response.get('tokens_spent')
                    atl_tokens_spent = llm_tokens / 3000
                    
                    # Log balance usage
                    balance_usage = await balance_usage_repo.create({
                        'user_id': user_id,
                        'organization_id': organization_id,
                        'balance_id': balance_id,
                        'input_text_count': len(user_message),
                        'gpt_token_spent': llm_tokens,
                        'input_token_count': llm_tokens,
                        'file_count': 1 if file else 0,
                        'file_size': file.size if file else None,
                        'atl_token_spent': atl_tokens_spent
                    })
                    print(balance_usage)
                    # Withdraw balance
                    withdraw_result = await balance_repo.withdraw_balance(organization_id, atl_tokens_spent)
                    print(withdraw_result)
                    if not withdraw_result:
                        raise ValueError("Failed to withdraw balance: insufficient funds or other issue")
                    
                    # Update task result
                    await bg_session.update_task_result(
                        task_id=task_id,
                        result_data=response.get('llm_response'),
                        tokens_spent=llm_tokens,
                        status="completed"
                    )
                    
                    # The transaction will be automatically committed here if no exceptions occurred
                    
                except Exception as e:
                    logging.error(f"Task failed: {str(e)}")
                    # The transaction will be automatically rolled back
                    await bg_session.update_task_result(
                        task_id=task_id,
                        result_data={"error": str(e)},
                        tokens_spent=0,
                        status="failed"
                    )
                    raise  # Re-raise the exception to ensure the transaction is rolled back