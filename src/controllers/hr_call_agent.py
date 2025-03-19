import os

import requests
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client


class HRCallAgent:
    def __init__(self, session: AsyncSession):
        self.TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
        self.TWILIO_SECRET = os.getenv("TWILIO_SECRET")
        self.TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        self.PLATFORM_BACKEND_URL = os.getenv("PLATFORM_BACKEND_URL")
        self.client = Client(self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN)
        self.TWILIO_PHONE_NUMBER = '+19159759046'
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.VOICE = 'Polly.Tatyana'
        self.LOG_EVENT_TYPES = [
            'error', 'response.content.done', 'rate_limits.updated',
            'response.done', 'input_audio_buffer.committed',
            'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
            'session.created'
        ]
        self.SYSTEM_MESSAGE = \
            """
            Ты – ИИ-рекрутер, который проводит первичный телефонный звонок кандидатам. Твоя задача — задать кандидату только те вопросы, которые указаны в списке questions_for_candidate, и ничего больше.
            questions_for_candidate: {}
            Твои инструкции:

            Приветствие и представление:
            Приветствие уже сказано, юзер должен тоже сказать приветствие и начни задавать вопросы
            
            Задание вопросов:
            Используя список вопросов из questions_for_candidate, задай их по порядку. Не добавляй никаких дополнительных вопросов, комментариев или пояснений. Если кандидат начинает говорить отклоняясь от темы, вежливо верни разговор к заданным вопросам.

            Фиксация ответов:
            Слушай ответы кандидата и, если необходимо, уточняй их только в пределах каждого вопроса, чтобы получить максимально точную информацию.

            Поддержание профессионализма:
            Используй деловой, уверенный и вежливый тон. Если кандидат задаёт вопросы, не связанные с текущим интервью, аккуратно перенаправь его обратно к списку вопросов.

            Завершение звонка:
            После того как все вопросы заданы, вежливо поблагодари кандидата за уделённое время и сообщи, что с ним свяжутся для дальнейшей коммуникации.

            Следуй строго списку вопросов из questions_for_candidate и не задавай никаких вопросов, помимо них.
            """

        self.SHOW_TIMING_MATH = False

    def get_system_message(self, questions_for_candidate):
        return self.SYSTEM_MESSAGE.format(questions_for_candidate)

    async def recording_status(self, request: Request):
        """
        Получает статус записи звонка от Twilio и скачивает запись,
        когда она готова.
        """
        form_data = await request.form()

        recording_status = form_data.get("RecordingStatus")
        recording_sid = form_data.get("RecordingSid")
        recording_url = form_data.get("RecordingUrl")
        call_sid = form_data.get("CallSid")
        duration = form_data.get("RecordingDuration")

        print(f"Recording status update: {recording_status}")
        print(f"Recording SID: {recording_sid}")
        print(f"Call SID: {call_sid}")
        print(f"Duration: {duration} seconds")

        if recording_status == "completed" and recording_url:
            print(f"Recording URL: {recording_url}")
            try:

                if "?auth_token=" in recording_url:
                    recording_url = recording_url.split("?auth_token=")[0]

                response = requests.get(url=recording_url, auth=(self.TWILIO_ACCOUNT_SID, self.TWILIO_SECRET))
                print(f"Response status code: {response.status_code}")
                print(f"Response content: {response.content[:100]}")  # Первые 100 байт ответа

                if response.status_code == 200:
                    file_data = response.content
                    file_key = f"recordings/{call_sid}_{recording_sid}.mp3"
                    permanent_url, _ = await self.minio_service.upload_single_file(file_data, file_key)
                    await self.favorite_repo.update_favorite_resume(call_sid=call_sid,
                                                                    upd_data={"recording_file": file_key,
                                                                              "is_responded": True, "is_called": True})
                else:
                    print(f"Failed to download recording. Status code: {response.status_code}")

            except Exception as e:
                print(f"Error downloading recording: {e}")

        return HTMLResponse(content="Recording status received", status_code=200)
