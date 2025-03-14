

from fastapi import APIRouter,Depends, Form
from src.controllers.hr_agent import HRAgentController
from src.schemas.requests.user_feedback import UserFeedbackRequest
from src.models.role import RoleEnum
from src.controllers.user_feedback import UserFeedbackController
from src.core.factory import Factory
from src.schemas.requests.users import *
from src.schemas.responses.auth import *

from src.core.middlewares.auth_middleware import get_current_user,require_roles
import os
import json
import asyncio
import base64
import time
import requests
import websockets
from fastapi import FastAPI, WebSocket, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv
from twilio.rest import Client


phone_interview_router = APIRouter(prefix='/api/v1/phone_interview',tags=['PHONE INTERVIEW'])



@phone_interview_router.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """
    Обрабатывает входящий звонок и возвращает TwiML для подключения
    к media stream с включенной транскрипцией.
    """
    resume_id = request.query_params.get('resume_id')
    response = VoiceResponse()
    response.say("Подождите пока мы настраиваем подключение")
    response.pause(length=1)
    response.say("Отлично, соединение настроено, вы можете говорить")
    host = request.url.hostname
    connect = Connect()
    stream = Stream(url=f'wss://71dc-79-142-54-219.ngrok-free.app/api/v1/phone_interview/media-stream/{resume_id}')

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
async def media_stream(websocket: WebSocket,resume_id:int, hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):  

    # Ваш основной обработчик
    await hr_agent_controller.media_stream(websocket, (resume_id))

@phone_interview_router.post("/recording-status")
async def make_call(
    request:Request,
    hr_agent_controller: HRAgentController = Depends(Factory.get_hr_agent_controller),
):
    res = await hr_agent_controller.recording_status(request)
    return res

