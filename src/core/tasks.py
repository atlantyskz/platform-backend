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
from src.repositories import WhatsappInstanceRepository, CurrentWhatsappInstanceRepository
from src.repositories.balance import BalanceRepository
from src.repositories.balance_usage import BalanceUsageRepository
from src.repositories.favorite_resume import FavoriteResumeRepository
from src.repositories.interview_individual_question import InterviewIndividualQuestionRepository
from src.repositories.user_interaction_repository import UserInteractionRepository
from src.services.green_api_instance_cli import GreenApiInstanceCli
from src.services.request_sender import RequestSender

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Celery beat schedule
celery_app.conf.enable_utc = True
celery_app.conf.beat_schedule = {
    'process-expired-free-trials': {
        'task': 'tasks.process_expired_free_trials',
        'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
    },
}


@celery_app.task
def process_expired_free_trials():
    logger.info("Starting expired free trial processing for all balances...")
    return asyncio.run(_process_expired_free_trials())


async def _process_expired_free_trials():
    try:
        postgres = session_manager
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        processed_count = 0

        async with postgres.session() as session:
            async with session.begin():
                query = select(Balance).where(
                    and_(
                        Balance.free_trial.is_(True),
                        Balance.created_at <= one_day_ago
                    )
                )
                result = await session.execute(query)
                expired_trials = result.scalars().all()

                balance_repo = BalanceRepository(session)

                for balance in expired_trials:
                    logger.info(
                        "Processing expired trial for organization_id: %s",
                        balance.organization_id
                    )

                    await _apply_expired_trial_logic(balance_repo, balance)
                    processed_count += 1
                    await session.flush()

                logger.info("Processed %d expired free trials.", processed_count)
                return {"processed": processed_count}
    except Exception as exc:
        logger.error("Error processing expired free trials: %s", str(exc))
        raise


@shared_task
def free_trial_tracker(balance_id):
    logger.info("Starting expired free trial processing for balance_id=%s", balance_id)
    return asyncio.run(_process_single_free_trial(balance_id))


async def _process_single_free_trial(balance_id):
    try:
        postgres = session_manager

        async with postgres.session() as session:
            async with session.begin():
                query = select(Balance).where(Balance.id == balance_id)
                result = await session.execute(query)
                balance = result.scalar_one_or_none()

                if not balance:
                    logger.info("No balance found with id=%s", balance_id)
                    return

                balance_repo = BalanceRepository(session)
                await _apply_expired_trial_logic(balance_repo, balance)
                await session.flush()
    except Exception as exc:
        logger.error("Error processing expired trial for balance_id=%s: %s", balance_id, str(exc))
        raise


async def _apply_expired_trial_logic(balance_repo: BalanceRepository, balance: Balance):
    if balance.atl_tokens >= 15:
        await balance_repo.withdraw_balance(balance.organization_id, 15)
        logger.info("Reduced unused trial balance by 15 tokens.")
    else:
        await balance_repo.update_balance(balance.organization_id, {"atl_tokens": 0})
        logger.info("Set partially used trial balance to 0 tokens.")

    await balance_repo.update_balance(balance.organization_id, {"free_trial": False})


@celery_app.task
def generate_questions_task(session_id, user_id, assistant_id, user_organization_id, balance_id):
    return asyncio.run(
        _process_generate_questions(
            session_id=session_id,
            user_id=user_id,
            assistant_id=assistant_id,
            user_organization_id=user_organization_id,
            balance_id=balance_id
        )
    )


async def _process_generate_questions(session_id, user_id, assistant_id, user_organization_id, balance_id):
    try:
        postgres = session_manager
        request_sender = RequestSender()

        async with postgres.session() as session:
            favorite_repo = FavoriteResumeRepository(session)
            question_repo = InterviewIndividualQuestionRepository(session)
            balance_repo = BalanceRepository(session)
            balance_usage_repo = BalanceUsageRepository(session)

            resumes = await favorite_repo.get_favorite_resumes_by_session_id(session_id)
            if not resumes:
                logger.info("No favorite resumes found for session_id=%s", session_id)

            for resume_record in resumes:
                await _generate_questions_for_resume(
                    session_id,
                    user_id,
                    assistant_id,
                    user_organization_id,
                    balance_id,
                    resume_record,
                    request_sender,
                    favorite_repo,
                    question_repo,
                    balance_repo,
                    balance_usage_repo
                )

            await session.commit()

        await _update_redis_task_status(user_id, session_id, status="success")

    except Exception as exc:
        logger.error("Error processing generate questions: %s", str(exc))
        await _update_redis_task_status(user_id, session_id, status="failed")
        raise


async def _generate_questions_for_resume(
        session_id,
        user_id,
        assistant_id,
        user_organization_id,
        balance_id,
        resume_record,
        request_sender,
        favorite_repo,
        question_repo,
        balance_repo,
        balance_usage_repo
):
    resume_data = await favorite_repo.get_result_data_by_resume_id(resume_record.resume_id)
    candidate_info = "\n".join(f"{k}: {v}" for k, v in resume_data.items())

    balance = await balance_repo.get_balance(user_organization_id)
    if balance.atl_tokens < 5:
        error_msg = f"Недостаточно средств: имеется {balance.atl_tokens} токенов, требуется минимум 5."
        logger.error(error_msg)
        await _update_redis_task_status(user_id, session_id, status="failed")
        raise ValueError(error_msg)

    messages = [{"role": "user", "content": f"Candidate Resume:\n{candidate_info}"}]
    response_data = await _attempt_llm_request(
        request_sender,
        messages,
        max_attempts=3
    )

    if not response_data or "llm_response" not in response_data:
        error_msg = "Не удалось получить валидный ответ от LLM сервиса."
        logger.error(error_msg)
        return

    tokens_spent = response_data.get("tokens_spent", 0)
    llm_response_data = response_data["llm_response"]
    interview_questions = llm_response_data.get("interview_questions", [])

    for question in interview_questions:
        await question_repo.create_question({
            "session_id": session_id,
            "resume_id": resume_record.resume_id,
            "question_text": question.get("question_text", "")
        })

    atl_tokens_spent = round(tokens_spent / 3000, 2)
    await balance_usage_repo.create({
        "user_id": user_id,
        "assistant_id": assistant_id,
        "type": "generate individual questions",
        "organization_id": user_organization_id,
        "balance_id": balance_id,
        "input_text_count": len(candidate_info),
        "gpt_token_spent": tokens_spent,
        "input_token_count": tokens_spent,
        "file_count": 0,
        "file_size": None,
        "atl_token_spent": atl_tokens_spent
    })


async def _attempt_llm_request(request_sender, messages, max_attempts=3):
    for attempt in range(max_attempts):
        llm_response = await request_sender._send_request(
            llm_url='http://llm_service:8001/hr/generate_questions_for_candidate',
            data={"messages": messages}
        )
        if (
                isinstance(llm_response, dict)
                and "llm_response" in llm_response
                and not llm_response.get("error")
        ):
            return llm_response
        logger.warning("Attempt %d to get LLM response failed.", attempt + 1)
    return None


async def _update_redis_task_status(user_id, session_id, status):
    task_key = f"task:{user_id}:{session_id}"
    redis_task_id = await redis_client.get(task_key)
    if redis_task_id is not None:
        await redis_client.set(redis_task_id, status)


@celery_app.task
def bulk_send_whatsapp_message(session_id, user_id):
    logger.info("bulk_send_whatsapp_message called for session_id=%s.", session_id)
    asyncio.run(_process_send_whatsapp_messages(session_id, user_id))


async def _process_send_whatsapp_messages(
        session_id,
        user_id,
):
    postgres = session_manager

    async with postgres.session() as session:
        favorite_repo = FavoriteResumeRepository(session)
        whatsapp_instance_repo = WhatsappInstanceRepository(session)
        current_instance_repo = CurrentWhatsappInstanceRepository(session)
        user_interaction_repo = UserInteractionRepository(session)  # <-- добавим
        green_api_instance_client = GreenApiInstanceCli()

    current_instance_id = await current_instance_repo.get_current_instance_id(user_id)
    if not current_instance_id:
        logger.info("No current instance found for user_id=%s", user_id)
        return

    whatsapp_instance = await whatsapp_instance_repo.get_by_id(current_instance_id)
    if not whatsapp_instance:
        logger.info("WhatsApp instance not found by ID=%s", current_instance_id)
        return

    resumes = await favorite_repo.get_favorite_resumes_by_session_id(session_id)
    if not resumes:
        logger.info("No favorite resumes found for session_id=%s", session_id)
        return
    print(resumes)
    for resume_record in resumes:
        resume_data = resume_record.result_data.get("candidate_info", {})
        phone_number = resume_data.get("contacts", {}).get("phone_number", "")
        if not phone_number:
            phone_number = "77762838451"
        cleaned_number = "".join([i for i in phone_number if i.isdigit()])
        if cleaned_number.startswith("8"):
            cleaned_number = "7" + cleaned_number[1:]
        chat_id = f"{cleaned_number}@c.us"

        existing_interaction = await user_interaction_repo.get_not_answered_by_chat(
            chat_id, "RESUME_OFFER"
        )
        if existing_interaction:
            logger.info(
                "Skipping new message to %s, since there's an unanswered interaction id=%s",
                chat_id, existing_interaction.id
            )
            continue

        await green_api_instance_client.send_poll(
            data={
                "chat_id": chat_id,
                "message": "Добрый день! Мы рассмотрели ваше резюме. Хотите обсудить детали?",
                "options": [
                    {"optionName": "Продолжить"},
                    {"optionName": "Не интересует"}
                ]
            },
            instance_id=whatsapp_instance.instance_id,
            instance_token=whatsapp_instance.instance_token
        )

        await user_interaction_repo.create_interaction(
            chat_id=chat_id,
            session_id=session_id,
            message_type="RESUME_OFFER"
        )
        await session.commit()
