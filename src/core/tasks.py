import asyncio
import logging
from datetime import datetime, timedelta

from celery import shared_task
from celery.schedules import crontab
from sqlalchemy import and_
from sqlalchemy.future import select

from src.core.celery_config import celery_app
from src.core.databases import session_manager
from src.core.redis_cli import redis_client
from src.models.balance import Balance
from src.repositories.balance import BalanceRepository
from src.repositories.balance_usage import BalanceUsageRepository
from src.repositories.favorite_resume import FavoriteResumeRepository
from src.repositories.interview_individual_question import InterviewIndividualQuestionRepository
from src.services.request_sender import RequestSender

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Celery to use UTC timezone

# Define the periodic tasks (like cron jobs)
celery_app.conf.enable_utc = True

celery_app.conf.beat_schedule = {
    'process-expired-free-trials': {
        'task': 'tasks.process_expired_free_trials',
        'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
        # For testing, you might want to run more frequently
        # 'schedule': 60.0,  # Run every 60 seconds
    },
}


@celery_app.task
def process_expired_free_trials():
    """Process all free trials that have expired (older than 1 days)."""
    logger.info("Starting expired free trial processing")

    # Run the async function using asyncio
    return asyncio.run(_process_expired_free_trials_async())


async def _process_expired_free_trials_async():
    """Async implementation to process expired free trials."""
    try:
        postgres = session_manager
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        processed_count = 0

        async with postgres.session() as session:
            async with session.begin():
                # Find balances with active free trials created more than 1 days ago
                query = select(Balance).where(
                    and_(
                        Balance.free_trial == True,
                        Balance.created_at <= one_day_ago
                    )
                )

                result = await session.execute(query)
                expired_trials = result.scalars().all()
                balance_repo = BalanceRepository(session)

                for balance in expired_trials:
                    logger.info(f"Processing expired trial for organization_id: {balance.organization_id}")
                    # Apply the business logic:
                    if balance.atl_tokens >= 15:
                        await balance_repo.withdraw_balance(balance.organization_id, 15)
                        logger.info(f"Reduced unused trial balance from 100 to 10 tokens")

                    elif balance.atl_tokens < 15:
                        await balance_repo.update_balance(balance.organization_id, data={"atl_tokens": 0})
                        logger.info(f"Set partially used trial balance to 10 tokens")

                    await balance_repo.update_balance(balance.organization_id, data={"free_trial": False})

                    processed_count += 1
                    await session.flush()
                logger.info(f"Processed {processed_count} expired free trials")
                return {"processed": processed_count}
    except Exception as e:
        logger.error(f"Error processing expired trials: {str(e)}")
        raise


@shared_task
def free_trial_tracker(balance_id):
    """Process all free trials that have expired (older than 3 days)."""
    logger.info("Starting expired free trial processing")

    # Run the async function using asyncio
    return asyncio.run(_process_expired_free_trial_async(balance_id))


async def _process_expired_free_trial_async(balance_id):
    try:
        postgres = session_manager

        async with postgres.session() as session:
            async with session.begin():
                query = select(Balance).where(
                    and_(
                        Balance.id == balance_id,
                    )
                )

                result = await session.execute(query)
                balance = result.scalar_one_or_none()

                balance_repo = BalanceRepository(session)

                if balance.atl_tokens >= 15:
                    await balance_repo.withdraw_balance(balance.organization_id, 15)

                elif balance.atl_tokens < 15:
                    await balance_repo.update_balance(balance.organization_id, data={"atl_tokens": 0})

                await balance_repo.update_balance(balance.organization_id, data={"free_trial": False})
                await session.flush()
    except Exception as e:
        logger.error(f"Error processing expired trials: {str(e)}")
        raise


@celery_app.task
def generate_questions_task(session_id, user_id, assistant_id, user_organization_id, balance_id):
    result = asyncio.run(
        _process_generate_questions(
            session_id,
            user_id,
            assistant_id,
            user_organization_id,
            balance_id
        )
    )
    return result


async def _process_generate_questions(session_id, user_id, assistant_id, user_organization_id, balance_id):
    """
    Implementation that uses async DB sessions, async Redis, etc.
    """
    try:
        postgres = session_manager
        favorite_repo_cls = FavoriteResumeRepository
        question_repo_cls = InterviewIndividualQuestionRepository
        balance_usage_repo_cls = BalanceUsageRepository
        balance_repo = BalanceRepository

        async with postgres.session() as session:
            favorite_repo = favorite_repo_cls(session)
            question_repo = question_repo_cls(session)
            balance_repo = balance_repo(session)
            balance_usage_repo = balance_usage_repo_cls(session)

            resumes = await favorite_repo.get_favorite_resumes_by_session_id(session_id)
            request_sender = RequestSender()
            max_attempts = 3

            for resume_record in resumes:
                resume_data = await favorite_repo.get_result_data_by_resume_id(resume_record.resume_id)
                candidate_info = ""
                logger.info(f"Resuming {resume_record}")

                for key, value in resume_data.items():
                    candidate_info += f"{key}: {value}\n"

                balance = await balance_repo.get_balance(user_organization_id)
                if balance.atl_tokens < 5:
                    error_msg = f"Недостаточно средств: имеется {balance.atl_tokens} токенов, требуется минимум 5"
                    logging.error(error_msg)

                    task_key = f"task:{user_id}:{session_id}"

                    task_id = await redis_client.get(task_key)
                    if task_id is not None:
                        await redis_client.set(task_id, "failed")
                    raise ValueError(error_msg)

                messages = [
                    {"role": "user", "content": f"Candidate Resume: {candidate_info}"}
                ]

                attempt = 0
                response_data = None

                while attempt < max_attempts:
                    llm_response = await request_sender._send_request(
                        llm_url='http://llm_service:8001/hr/generate_questions_for_candidate',
                        data={"messages": messages}
                    )
                    if (
                            isinstance(llm_response, dict)
                            and "llm_response" in llm_response
                            and not llm_response.get("error")
                    ):
                        response_data = llm_response
                        break
                    else:
                        attempt += 1

                if attempt == max_attempts or not response_data or "llm_response" not in response_data:
                    error_msg = "Не удалось получить валидный ответ от LLM сервиса"
                    logger.error(error_msg)
                    continue

                tokens_spent = response_data.get("tokens_spent", 0)
                llm_response_data = response_data.get("llm_response", {})
                interview_questions = llm_response_data.get("interview_questions", [])

                for question in interview_questions:
                    await question_repo.create_question({
                        "session_id": session_id,
                        "resume_id": resume_record.resume_id,
                        "question_text": question.get("question_text", "")
                    })

                atl_tokens_spent = round(tokens_spent / 3000, 2)

                await balance_usage_repo.create({
                    'user_id': user_id,
                    "assistant_id": assistant_id,
                    "type": "generate individual questions",
                    'organization_id': user_organization_id,
                    'balance_id': balance_id,
                    'input_text_count': len(f"Candidate Resume: {resume_data}"),
                    'gpt_token_spent': tokens_spent,
                    'input_token_count': tokens_spent,
                    'file_count': 0,
                    'file_size': None,
                    'atl_token_spent': atl_tokens_spent
                })

            await session.commit()
        task_key = f"task:{user_id}:{session_id}"
        if task_id is not None:
            task_id = await redis_client.get(task_key)
        await redis_client.set(task_id, "success")

    except Exception as e:
        logger.error(f"Error processing generate questions: {str(e)}")
        task_key = f"task:{user_id}:{session_id}"
        task_id = await redis_client.get(task_key)
        if task_id is not None:
            await redis_client.set(task_id, "failed")

        raise e



@celery_app.task
def bulk_send_whatsapp_message(session_id, ):
    pass