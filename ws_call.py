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

load_dotenv()

TWILIO_PHONE_NUMBER = '+19159759046'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = 8000
SYSTEM_MESSAGE = (
    "You are a helpful and bubbly AI assistant who loves to chat about "
    "anything the user is interested in and is prepared to offer them facts. "
    "You have a penchant for dad jokes, owl jokes, and rickrolling – subtly. "
    "Always stay positive, but work in a joke when appropriate."
)
VOICE = 'alloy'
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created'
]
SHOW_TIMING_MATH = False


app = FastAPI()

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

client = Client(username=TWILIO_ACCOUNT_SID, password=TWILIO_SECRET)

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """
    Обрабатывает входящий звонок и возвращает TwiML для подключения
    к media stream с включенной транскрипцией.
    """
    user_id = request.query_params.get('user_id')
    response = VoiceResponse()
    response.say("Подождите пока мы настраиваем подключение")
    response.pause(length=1)
    response.say("Отлично, соединение настроено, вы можете говорить")
    response.record(transcribe=True)
    response.hangup()
    connect = Connect()
    stream = Stream(url=f'wss://{NGROK_URL}/media-stream?user_id={user_id}')
    connect.append(stream)
    response.append(connect)
    
    return HTMLResponse(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket,):
    """
    Обрабатывает соединение WebSocket между Twilio и OpenAI.
    Аудио от клиента и ИИ буферизуется и, по завершению сегмента,
    сохраняется в отдельные аудио файлы.
    """
    print("Client connected")
    user_id = await websocket.query_params.get('user_id')
    custum_prompt = await self.user_repo.fetch_prompt_by_userid(user_id)
    await websocket.accept()

    # Буферы для аудио клиента и ИИ
    client_audio_buffer = bytearray()
    ai_audio_buffer = bytearray()

    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1",
        }
    ) as openai_ws:
        await initialize_session(openai_ws,custum_prompt)
        await send_initial_conversation_item(openai_ws)
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None

        async def receive_from_twilio():
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    # Если получено аудио от клиента – сохраняем в буфер и пересылаем в OpenAI
                    if data['event'] == 'media' and openai_ws.open:
                        latest_media_timestamp = int(data['media']['timestamp'])
                        payload = data['media']['payload']
                        decoded_audio = base64.b64decode(payload)
                        client_audio_buffer.extend(decoded_audio)
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": payload
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
            try:
                async for openai_message in openai_ws:
                    response_data = json.loads(openai_message)
                    if response_data['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response_data['type']}", response_data)

                    # При получении аудио-дельты от ИИ – сохраняем в буфер и пересылаем в Twilio
                    if response_data.get('type') == 'response.audio.delta' and 'delta' in response_data:
                        delta_payload = response_data['delta']
                        delta_decoded = base64.b64decode(delta_payload)
                        ai_audio_buffer.extend(delta_decoded)
                        audio_payload = base64.b64encode(delta_decoded).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": audio_payload}
                        }
                        await websocket.send_json(audio_delta)

                        if response_start_timestamp_twilio is None:
                            response_start_timestamp_twilio = latest_media_timestamp
                            if SHOW_TIMING_MATH:
                                print(
                                    f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms"
                                )

                        if response_data.get('item_id'):
                            last_assistant_item = response_data['item_id']

                        await send_mark(websocket, stream_sid)

                    # По завершении ответа ИИ – сохраняем накопленный аудио буфер в файл
                    if response_data.get('type') == 'response.done':
                        timestamp = int(time.time() * 1000)
                        filename = f"ai_audio_{timestamp}.ulaw"
                        with open(filename, "wb") as f:
                            f.write(ai_audio_buffer)
                        print(f"Saved AI audio to {filename}")
                        ai_audio_buffer.clear()

                    if response_data.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            nonlocal response_start_timestamp_twilio, last_assistant_item
            print("Handling speech started event.")
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                if SHOW_TIMING_MATH:
                    print(
                        f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms"
                    )
                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        print(
                            f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms"
                        )
                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))
                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })
                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                }
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

@app.post("/recording-status")
async def recording_status(request: Request):
    """
    Получает статус записи звонка от Twilio и скачивает запись, 
    когда она готова.
    """
    form_data = await request.form()
    print("FORM_DATA", form_data)
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
        
        # Скачиваем запись
        timestamp = int(time.time())
        RECORDINGS_FOLDER = 'recordings'
        file_path = f"{RECORDINGS_FOLDER}/call_{call_sid}_{timestamp}.mp3"
        
        try:
            
            # Убедимся, что recording_url не содержит auth_token
            if "?auth_token=" in recording_url:
                recording_url = recording_url.split("?auth_token=")[0]
            
            response = requests.get(url=recording_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_SECRET))
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.content[:100]}")  # Первые 100 байт ответа
            
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"Successfully downloaded recording to {file_path}")
            else:
                print(f"Failed to download recording. Status code: {response.status_code}")
            
        except Exception as e:
            print(f"Error downloading recording: {e}")
            
    return HTMLResponse(content="Recording status received", status_code=200)


async def send_initial_conversation_item(openai_ws):
    """Отправляет начальный элемент диалога, чтобы ИИ мог начать разговор."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Привет! Я голосовой AI-ассистент от Atlantys AI. Чем могу помочь?"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))

async def initialize_session(openai_ws,custum_prompt):
    """Инициализирует сессию с OpenAI, отправляя настройки сессии."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": custum_prompt,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

@app.post("/make-call")
async def make_call(phone_number: str = Form(...),user_id:str = Form(...)):
    """Инициирует звонок на указанный номер и включает запись разговора."""
    
    call = client.calls.create(
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        url=f"https://{NGROK_URL}/incoming-call?user_id={user_id}",
        record=True,  
        recording_status_callback=f"https://{NGROK_URL}/recording-status",
        recording_status_callback_method="POST",
        recording_channels="mono",
    )   
    return {"message": "Call initiated", "call_sid": call.sid}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("ws_call:app", port=PORT, host="0.0.0.0", reload=True)