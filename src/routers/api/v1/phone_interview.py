from fastapi import APIRouter, Depends
from fastapi import WebSocket, Request, Form
from fastapi.responses import HTMLResponse
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

from src.controllers.hr_agent import HRAgentController
from src.core.factory import Factory

phone_interview_router = APIRouter(prefix='/api/v1/phone_interview', tags=['PHONE INTERVIEW'])


@phone_interview_router.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """
    Обрабатывает входящий звонок и возвращает TwiML для подключения
    к media stream с включенной транскрипцией.
    """
    resume_id = request.query_params.get('resume_id')
    response = VoiceResponse()
    connect = Connect()
    stream = Stream(url=f'wss://api.atlantys.kz/api/v1/phone_interview/media-stream/{resume_id}')
    response.record(transcribe=True)
    connect.append(stream)
    response.append(connect)

    return HTMLResponse(content=str(response), media_type="application/xml")


@phone_interview_router.post("/make-call")
async def make_call(
        resume_id: int = Form(...),
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    res = await hr_agent_controller.make_call(resume_id)
    return res


@phone_interview_router.websocket('/media-stream/{resume_id}')
async def media_stream(websocket: WebSocket, resume_id: int,
                       hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
                       ):
    # Ваш основной обработчик
    await hr_agent_controller.media_stream(websocket, (resume_id))


@phone_interview_router.post("/recording-status")
async def make_call(
        request: Request,
        hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    res = await hr_agent_controller.recording_status(request)
    return res
