import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import BOT_TOKEN, WEB_APP_URL, OWNER_CHAT_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

WEBHOOK_PATH = "/webhook"
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "3000"))
WEBAPP_DIR = Path(__file__).parent / "webapp"

# Базовый URL бота (https://bot-xxx.bothost.tech)
_parsed = urlparse(WEB_APP_URL)
BASE_URL = f"{_parsed.scheme}://{_parsed.netloc}"


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEB_APP_URL))]
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Нажми кнопку ниже, чтобы призвать питание",
        reply_markup=main_keyboard(),
    )


@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    try:
        raw_data = message.web_app_data.data
        data = json.loads(raw_data)

        items = data.get("items", [])
        user_name = data.get("user_name", "Кто-то")
        note = data.get("note", "").strip()

        if not items:
            await message.answer("Ты ничего не выбрала 🥺")
            return

        lines = [
            f"• {item.get('title', 'Без названия')} — {item.get('place', 'Без места')}"
            for item in items
        ]
        text_for_owner = (
            f"ХОЧУ от {user_name}\n\n"
            f"Выбрано:\n" + "\n".join(lines)
        )
        if note:
            text_for_owner += f"\n\nКомментарий: {note}"

        await bot.send_message(OWNER_CHAT_ID, text_for_owner)
        await message.answer("Запрос отправлен")

    except Exception as e:
        logger.exception("Failed to process web app data")
        await message.answer(f"Ошибка обработки данных: {e}")


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "status": "running"})


async def on_startup(app: web.Application) -> None:
    webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"
    logger.info(f"Setting webhook: {webhook_url}")
    await bot.set_webhook(webhook_url)
    logger.info("Webhook set OK")


async def on_shutdown(app: web.Application) -> None:
    logger.info("Deleting webhook...")
    await bot.delete_webhook()
    await bot.session.close()


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty")
    if not WEB_APP_URL:
        raise RuntimeError("WEB_APP_URL is empty")
    if not OWNER_CHAT_ID:
        raise RuntimeError("OWNER_CHAT_ID is empty")

    app = web.Application()

    # Health check
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)

    # Mini App — статические файлы
    if WEBAPP_DIR.exists():
        app.router.add_static("/webapp", path=str(WEBAPP_DIR), show_index=True)
        logger.info(f"Serving webapp from {WEBAPP_DIR}")

    # Telegram webhook
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    logger.info(f"Starting server on {HOST}:{PORT}")
    web.run_app(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
