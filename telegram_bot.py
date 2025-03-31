import asyncio
import os

import dotenv
import httpx
import uvicorn
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, BotCommand
from fastapi import FastAPI, Form

dotenv.load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
router = Router()

app = FastAPI()

BACKEND_URL = "http://platform-backend:9000/"

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="health", description="Check if the bot is running"),
        BotCommand(command="active", description="Activate promocode: /active <user_id>"),
        BotCommand(command="deactive", description="Deactivate promocode: /deactive <user_id>"),
    ]
    await bot.set_my_commands(commands)

@router.message(Command("health"))
async def health_check(message: Message, bot: Bot):
    """Simple health check for Telegram bot."""
    await message.answer("Telegram bot is running")


@router.message(Command("active"))
async def active_promocode(message: Message, bot: Bot):
    """Activate promocode for a user."""
    try:
        user_id = message.text.split(" ", maxsplit=1)[1]
    except IndexError:
        await message.answer("❌ Usage: /active <user_id>")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BACKEND_URL}/api/v1/promocode/update/{user_id}",
                data={"is_active": True}
            )
        if response.status_code == 200:
            await message.answer(f"✅ Promocode for user `{user_id}` activated.", parse_mode="Markdown")
        else:
            await message.answer(f"❌ Failed to activate promocode. Server returned status {response.status_code}.")
    except httpx.RequestError as e:
        await message.answer(f"❌ HTTP error occurred: {e}")


@router.message(Command("deactive"))
async def deactive_promocode(message: Message, bot: Bot):
    """Deactivate promocode for a user."""
    try:
        user_id = message.text.split(" ", maxsplit=1)[1]
    except IndexError:
        await message.answer("❌ Usage: /deactive <user_id>")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BACKEND_URL}/api/v1/promocode/update/{user_id}",
                data={"is_active": False}
            )
        if response.status_code == 200:
            await message.answer(f"✅ Promocode for user `{user_id}` deactivated.", parse_mode="Markdown")
        else:
            await message.answer(f"❌ Failed to deactivate promocode. Server returned status {response.status_code}.")
    except httpx.RequestError as e:
        await message.answer(f"❌ HTTP error occurred: {e}")


dp.include_router(router)


@app.post("/send_alert")
async def send_alert(error_message: str = Form()):
    """Sends an alert message to all registered Telegram chats."""
    chat_ids = ["-1002270969400"]

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
    await set_bot_commands(bot)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def start_fastapi_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=9010)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(
        start_telegram_bot(),
        start_fastapi_server(),
    )


if __name__ == "__main__":
    asyncio.run(main())
