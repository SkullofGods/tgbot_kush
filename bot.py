import asyncio
import json
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
)

from config import BOT_TOKEN, WEB_APP_URL, OWNER_CHAT_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🍽 Открыть меню",
                    web_app=WebAppInfo(url=WEB_APP_URL),
                )
            ]
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Нажми кнопку ниже, чтобы открыть меню хотелок 🍓",
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

        lines = []
        for item in items:
            title = item.get("title", "Без названия")
            place = item.get("place", "Без места")
            lines.append(f"• {title} — {place}")

        text_for_owner = (
            f"💌 Новая хотелка от {user_name}\n\n"
            f"Выбрано:\n" + "\n".join(lines)
        )

        if note:
            text_for_owner += f"\n\nКомментарий: {note}"

        await bot.send_message(OWNER_CHAT_ID, text_for_owner)
        await message.answer("Готово! Я отправил список ему 💖")

    except Exception as e:
        logging.exception("Failed to process web app data")
        await message.answer(f"Ошибка обработки данных: {e}")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty")
    if not WEB_APP_URL:
        raise RuntimeError("WEB_APP_URL is empty")
    if not OWNER_CHAT_ID:
        raise RuntimeError("OWNER_CHAT_ID is empty")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())