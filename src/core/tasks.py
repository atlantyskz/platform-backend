import asyncio
import json
import logging
from datetime import datetime, timedelta

from celery import shared_task
from celery.schedules import crontab
from sqlalchemy import and_
from sqlalchemy.future import select

from src.core.celery_config import celery_app
from src.core.databases import session_manager
from src.core.redis_cli import redis_client
from src.models import GenerateStatus
from src.models.balance import Balance
from src.repositories import WhatsappInstanceRepository, CurrentWhatsappInstanceRepository, OrganizationRepository
from src.repositories.balance import BalanceRepository
from src.repositories.balance_usage import BalanceUsageRepository
from src.repositories.favorite_resume import FavoriteResumeRepository
from src.repositories.interview_individual_question import InterviewIndividualQuestionRepository
from src.repositories.question_generate_session import QuestionGenerateSessionRepository
from src.repositories.user_interaction_repository import UserInteractionRepository
from src.repositories.vacancy import VacancyRepository
from src.services.green_api_instance_cli import GreenApiInstanceCli
from src.services.request_sender import RequestSender
from src.services.websocket import manager

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
def generate_questions_task(
        session_id,
        user_id,
        assistant_id,
        user_organization_id,
        balance_id
):
    return asyncio.run(
        _process_generate_questions(
            session_id=session_id,
            user_id=user_id,
            assistant_id=assistant_id,
            user_organization_id=user_organization_id,
            balance_id=balance_id
        )
    )


async def _process_generate_questions(
        session_id,
        user_id,
        assistant_id,
        user_organization_id,
        balance_id
):
    postgres = session_manager
    question_generate_session_repo = None

    try:
        async with postgres.session() as session:
            favorite_repo = FavoriteResumeRepository(session)
            question_repo = InterviewIndividualQuestionRepository(session)
            balance_repo = BalanceRepository(session)
            balance_usage_repo = BalanceUsageRepository(session)
            question_generate_session_repo = QuestionGenerateSessionRepository(session)

            resumes = await favorite_repo.get_favorite_resumes_by_session_id(session_id)
            if not resumes:
                logger.info("No favorite resumes found for session_id=%s", session_id)

            for index, resume_record in enumerate(resumes):
                print(resume_record)
                await _generate_questions_for_resume(
                    session_id,
                    user_id,
                    assistant_id,
                    user_organization_id,
                    balance_id,
                    resume_record,
                    question_repo,
                    balance_repo,
                    balance_usage_repo,
                    session
                )

                await manager.notify_progress(session_id, {
                    "resume_id": resume_record.id,
                    "status": "done",
                    "current": index + 1,
                    "total": len(resumes),
                    "percentage": round((index + 1) / len(resumes) * 100)
                })
                await session.flush()

            await question_generate_session_repo.update_status(session_id, GenerateStatus.SUCCESS)
            await session.commit()

    except Exception as exc:
        logger.error("Error processing generate questions for session_id=%s: %s", session_id, str(exc))
        if question_generate_session_repo:
            async with postgres.session() as session:
                repo = QuestionGenerateSessionRepository(session)
                await repo.update_status(session_id, GenerateStatus.FAILURE)
        raise


async def _generate_questions_for_resume(
        session_id,
        user_id,
        assistant_id,
        user_organization_id,
        balance_id,
        resume_record,
        question_repo,
        balance_repo,
        balance_usage_repo,
        session
):
    try:
        resume_data = resume_record.result_data.get("candidate_info", {})
        candidate_info = "\n".join(f"{k}: {v}" for k, v in resume_data.items())

        balance = await balance_repo.get_balance(user_organization_id)
        if balance.atl_tokens < 5:
            error_msg = f"Недостаточно средств: имеется {balance.atl_tokens} токенов, требуется минимум 5."
            logger.error(error_msg)
            await _update_redis_task_status(user_id, session_id, status="failed")
            raise ValueError(error_msg)

        messages = [{"role": "user", "content": f"Candidate Resume:\n{candidate_info}"}]
        response_data = await _attempt_llm_request(
            messages,
            max_attempts=3
        )
        print(response_data, "\n\n\n\n")
        tokens_spent = response_data.get("tokens_spent", 0)
        llm_response_data = response_data["llm_response"]
        interview_questions = llm_response_data.get("interview_questions", [])

        for question in interview_questions:
            print(question, "\n\n\n")
            print("Question Text",question.get("question_text", ""))
            await question_repo.create_question({
                "resume_id": resume_record.id,
                "question_text": question.get("question_text", "")
            })
            await session.flush()

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
        await session.flush()
    except Exception as exc:
        logger.error("Error processing interview questions: %s", str(exc))


async def _attempt_llm_request(messages, max_attempts=3):
    for attempt in range(max_attempts):
        response_data = await RequestSender()._send_request(
            llm_url='http://llm_service:8001/hr/generate_questions_for_candidate',
            data={"messages": messages}
        )
        if not response_data or "llm_response" not in response_data or response_data.get("error"):
            raise ValueError("Некорректный ответ от LLM")

        return response_data
    return None


async def _update_redis_task_status(user_id, session_id, status):
    task_key = f"task:{user_id}:{session_id}"
    redis_task_id = await redis_client.get(task_key)
    if redis_task_id is not None:
        await redis_client.set(redis_task_id, status)


@celery_app.task
def bulk_send_whatsapp_message(session_id, user_id):
    asyncio.run(_process_send_whatsapp_messages(session_id, user_id))


async def _process_send_whatsapp_messages(
        session_id: str,
        user_id: int
) -> None:
    postgres = session_manager

    async with postgres.session() as session:
        favorite_repo = FavoriteResumeRepository(session)
        whatsapp_instance_repo = WhatsappInstanceRepository(session)
        current_instance_repo = CurrentWhatsappInstanceRepository(session)
        user_interaction_repo = UserInteractionRepository(session)
        organization_repo = OrganizationRepository(session)
        vacancy_repo = VacancyRepository(session)

        green_api_instance_client = GreenApiInstanceCli()

        current_instance_id = await current_instance_repo.get_current_instance_id(user_id)
        if not current_instance_id:
            logger.info("Не найден текущий WhatsApp-инстанс для user_id=%s", user_id)
            return

        whatsapp_instance = await whatsapp_instance_repo.get_by_id(current_instance_id)
        if not whatsapp_instance:
            logger.info("WhatsApp-инстанс не найден по ID=%s", current_instance_id)
            return

        resumes = await favorite_repo.get_favorite_resumes_by_session_id(session_id)
        if not resumes:
            logger.info("Нет избранных резюме для session_id=%s", session_id)
            return

        organization = await organization_repo.get_user_organization(user_id)
        vacancy = await vacancy_repo.get_by_session_id(session_id)

        ignored = []
        for resume_record in resumes:
            resume_data = resume_record.result_data.get("candidate_info", {})
            full_name = resume_data.get("fullname", "")
            phone_number = resume_data.get("contacts", {}).get("phone_number", "")

            if not phone_number:
                phone_number = "77762838451"

            cleaned_number = "".join(ch for ch in phone_number if ch.isdigit())
            if cleaned_number.startswith("8"):
                cleaned_number = "7" + cleaned_number[1:]
            chat_id = f"{cleaned_number}@c.us"

            session_interaction = await user_interaction_repo.get_interaction_by_session_id(chat_id, session_id)
            if session_interaction:
                continue

            existing_interaction = await user_interaction_repo.get_interaction_by_chat_id(
                chat_id,
                whatsapp_instance.id
            )

            if existing_interaction:
                if (
                        not existing_interaction.is_answered
                        and
                        datetime.utcnow() < existing_interaction.created_at + timedelta(hours=24)
                ):
                    logger.info(
                        "Пропускаем отправку нового сообщения на %s, т.к. есть неотвеченное взаимодействие с id=%s",
                        chat_id,
                        existing_interaction.id
                    )
                    ignored.append(existing_interaction.id)
                    await redis_client.set(
                        f"session-ignored-chats:{session_id}",
                        json.dumps(ignored),
                        ex=86400
                    )
                    continue
                else:
                    text_message = (
                        f"Здравствуйте, {full_name}! Это AI рекрутер из компании {organization.name}. "
                        f"Рады снова с Вами связаться. Вы откликнулись на нашу вакансию «{vacancy.title}», "
                        f"и мы были бы рады обсудить дальнейшие шаги лично. Напишите, пожалуйста, если у Вас возникли вопросы."
                    )
            else:
                text_message = (
                    f"Добрый день, {full_name}! Я — AI-рекрутер компании {organization.name}.\n"
                    f"Вы откликались на нашу вакансию «{vacancy.title}». Мы внимательно изучили ваше резюме "
                    f"и хотели бы обсудить дальнейшие шаги. \n\n"
                    f"Напишите 1, чтобы продолжить, или 2, если не хотите продолжать общение."
                )

            await green_api_instance_client.send_message(
                data={
                    "chat_id": chat_id,
                    "message": text_message
                },
                instance_id=whatsapp_instance.instance_id,
                instance_token=whatsapp_instance.instance_token
            )

            await user_interaction_repo.create_interaction(
                chat_id=chat_id,
                instance_id=whatsapp_instance.id,
                session_id=session_id,
                message_type="RESUME_OFFER"
            )

            await session.commit()


@celery_app.task
def bulk_resend_whatsapp_message(session_id, user_id):
    asyncio.run(_process_resend_whatsapp_messages(session_id, user_id))


async def _process_resend_whatsapp_messages(session_id: str, user_id: int) -> None:
    postgres = session_manager

    async with postgres.session() as session:
        whatsapp_instance_repo = WhatsappInstanceRepository(session)
        current_instance_repo = CurrentWhatsappInstanceRepository(session)
        user_interaction_repo = UserInteractionRepository(session)
        vacancy_repo = VacancyRepository(session)
        organization_repo = OrganizationRepository(session)

        green_api_instance_client = GreenApiInstanceCli()
        current_instance_id = await current_instance_repo.get_current_instance_id(user_id)
        if not current_instance_id:
            logger.info("Не найден текущий WhatsApp-инстанс для user_id=%s", user_id)
            return

        whatsapp_instance = await whatsapp_instance_repo.get_by_id(current_instance_id)
        if not whatsapp_instance:
            logger.info("WhatsApp-инстанс не найден по ID=%s", current_instance_id)
            return

        vacancy = await vacancy_repo.get_by_session_id(session_id)
        organization = await organization_repo.get_user_organization(user_id)

        redis_key = f"session-ignored-chats:{session_id}"
        ignored_data = await redis_client.get(redis_key)
        if not ignored_data:
            logger.info("Нет игнорируемых чатов для сессии %s", session_id)
            return

        try:
            ignored_chats = json.loads(ignored_data)
        except Exception as e:
            logger.error("Ошибка загрузки игнорируемых чатов: %s", str(e))
            return
        resend_message = (
            f"Здравствуйте! Вы откликались на вакансию «{vacancy.title}» "
            f"в компании {organization.name}. Если у вас есть вопросы или вы хотите обсудить дальнейшие шаги, "
            "пожалуйста, напишите «1». Если не хотите продолжать общение — напишите «2»."
        )
        for chat_id in ignored_chats:
            try:
                existing_interaction = await user_interaction_repo.get_interaction_by_chat_id(
                    chat_id,
                    whatsapp_instance.id
                )

                await user_interaction_repo.update_interaction(
                    existing_interaction.chat_id,
                    existing_interaction.instance_id,
                    {
                        "is_last": False
                    }
                )

                await green_api_instance_client.send_message(
                    data={
                        "chat_id": chat_id,
                        "message": resend_message
                    },
                    instance_id=whatsapp_instance.instance_id,
                    instance_token=whatsapp_instance.instance_token
                )
                await user_interaction_repo.create_interaction(
                    chat_id=chat_id,
                    instance_id=whatsapp_instance.id,
                    session_id=session_id,
                    message_type="RESUME_OFFER"
                )
                logger.info("Повторное сообщение отправлено на %s", chat_id)
            except Exception as e:
                logger.error("Ошибка при повторной отправке сообщения для %s: %s", chat_id, str(e))
        await redis_client.delete(redis_key)
        await session.commit()
