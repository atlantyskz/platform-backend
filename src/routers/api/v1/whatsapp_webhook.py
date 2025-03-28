from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/green-api", tags=["whatsapp"])


@router.post("/whatsapp-webhook")
async def post_whatsapp_webhook(request: Request):
    data = await request.json()
    if not data:
        return JSONResponse({"error": "No data"}, status_code=400)

    if data.get('typeWebhook') == 'incomingMessageReceived':
        sender = data.get('senderData', {}).get('sender')
        message = data.get('messageData', {}).get('textMessageData', {}).get('textMessage')

        print(f"New message from {sender}: {message}")

    return JSONResponse({'status': 'received'}, status_code=200)
