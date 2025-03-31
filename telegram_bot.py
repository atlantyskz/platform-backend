import asyncio
import os

import dotenv
import uvicorn
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from fastapi import FastAPI, BackgroundTasks, Form

dotenv.load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
router = Router()

app = FastAPI()


@router.message(Command("health"))
async def health_check(message: Message, bot: Bot):
    """Simple health check for Telegram bot."""
    await message.answer("Telegram bot is running")


dp.include_router(router)


@app.post("/send_alert")
async def send_alert(error_message: str = Form()):
    """Sends an alert message to all registered Telegram chats."""
    chat_ids = ["-2270969400"]
    async def send_messages():
        for chat_id in chat_ids:
            try:
                print(f"📩 Sending alert to {chat_id}...")
                await bot.send_message(chat_id, error_message)
                print(f"✅ Successfully sent alert to {chat_id}")
            except Exception as e:
                print(f"❌ Failed to send message to {chat_id}: {e}")

    asyncio.create_task(send_messages())

    return {"status": "ok", "message": "Alert sending started"}


async def start_telegram_bot():
    print("Starting Telegram Bot...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def start_fastapi_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=9005)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(
        start_telegram_bot(),
        start_fastapi_server(),
    )


if __name__ == "__main__":
    asyncio.run(main())
