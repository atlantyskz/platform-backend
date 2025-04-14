import logging
from datetime import datetime, timedelta

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import time_limit
from dramatiq.middleware.asyncio import AsyncIO

from src.core.databases import session_manager
from src.models import GenerateStatus
from src.repositories.balance import BalanceRepository
from src.repositories.balance_usage import BalanceUsageRepository
from src.services.request_sender import RequestSender
from src.services.websocket import manager

logger = logging.getLogger(__name__)

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

    @staticmethod
    @dramatiq.actor(max_retries=1)
    async def generate_questions_task(
            session_id,
            user_id,
            assistant_id,
            user_organization_id,
            balance_id
    ):
        from src.core.databases import session_manager
        from src.repositories import (
            FavoriteResumeRepository,
            InterviewIndividualQuestionRepository,
            QuestionGenerateSessionRepository,
            BalanceRepository,
            BalanceUsageRepository,
        )

        try:
            async with session_manager.session() as session:
                favorite_repo = FavoriteResumeRepository(session)
                question_repo = InterviewIndividualQuestionRepository(session)
                balance_repo = BalanceRepository(session)
                balance_usage_repo = BalanceUsageRepository(session)
                question_generate_session_repo = QuestionGenerateSessionRepository(session)

                resumes = await favorite_repo.get_favorite_resumes_by_session_id(session_id)
                if not resumes:
                    logger.info("No favorite resumes found for session_id=%s", session_id)
                    return

                for index, resume_record in enumerate(resumes):
                    try:
                        async with session.begin_nested():
                            resume_data = resume_record.result_data.get("candidate_info", {})
                            candidate_info = "\n".join(f"{k}: {v}" for k, v in resume_data.items())

                            balance = await balance_repo.get_balance(user_organization_id)
                            if balance.atl_tokens < 5:
                                raise ValueError(f"Недостаточно средств: {balance.atl_tokens} токенов < 5")

                            response_data = await DramatiqWorker._attempt_llm_request(
                                [{"role": "user", "content": f"Candidate Resume:\n{candidate_info}"}]
                            )
                            tokens_spent = response_data.get("tokens_spent", 0)
                            llm_response_data = response_data["llm_response"]
                            interview_questions = llm_response_data.get("interview_questions", [])

                            resume_obj = await favorite_repo.get_favorite_resumes_by_resume_id(resume_record.id)
                            if not resume_obj:
                                continue

                            questions_to_insert = [
                                {"resume_id": resume_obj.id, "question_text": q.get("question_text", "")}
                                for q in interview_questions
                            ]
                            await question_repo.bulk_insert_questions(questions_to_insert)

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

                            await manager.notify_progress(session_id, {
                                "resume_id": resume_record.id,
                                "status": "done",
                                "current": index + 1,
                                "total": len(resumes),
                                "percentage": round((index + 1) / len(resumes) * 100)
                            })

                    except Exception as e:
                        logger.error("Error processing resume %s: %s", resume_record.id, str(e))
                        continue

                await question_generate_session_repo.update_status(session_id, GenerateStatus.SUCCESS)
                await session.commit()

        except Exception as exc:
            logger.error("Global error in generate_questions_task: %s", str(exc))
            async with session_manager.session() as session:
                repo = QuestionGenerateSessionRepository(session)
                await repo.update_status(session_id, GenerateStatus.FAILURE, str(exc))
                await session.commit()

    @staticmethod
    @dramatiq.actor
    async def bulk_send_whatsapp_message(
            session_id,
            user_id
    ):
        from src.repositories import FavoriteResumeRepository
        from src.repositories import WhatsappInstanceRepository
        from src.repositories import CurrentWhatsappInstanceRepository
        from src.repositories import UserInteractionRepository
        from src.repositories import OrganizationRepository
        from src.repositories import VacancyRepository
        from src.services.green_api_instance_cli import GreenApiInstanceCli

        async with session_manager.session() as session:
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
                        await user_interaction_repo.update_interaction(chat_id, existing_interaction,
                                                                       {"is_ignored": True})
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

    @staticmethod
    @dramatiq.actor
    async def bulk_resend_whatsapp_message(session_id, user_id):
        from src.repositories import CurrentWhatsappInstanceRepository
        from src.repositories import UserInteractionRepository
        from src.repositories import WhatsappInstanceRepository
        from src.repositories import VacancyRepository
        from src.repositories import OrganizationRepository
        from src.services.green_api_instance_cli import GreenApiInstanceCli

        async with session_manager.session() as session:
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

            ignored_chats = await user_interaction_repo.get_ignored_interactions(
                session_id=session_id
            )
            if not ignored_chats:
                logger.info("Нет игнорируемых чатов для сессии %s", session_id)
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
            await session.commit()

    @classmethod
    async def _attempt_llm_request(cls, messages, max_attempts=3):
        last_error = None
        for attempt in range(max_attempts):
            response_data = await RequestSender()._send_request(
                llm_url='http://llm_service:8001/hr/generate_questions_for_candidate',
                data={"messages": messages}
            )
            if response_data and "llm_response" in response_data and not response_data.get("error"):
                return response_data
            last_error = ValueError("Некорректный ответ от LLM")
        if last_error:
            raise last_error
        return None
