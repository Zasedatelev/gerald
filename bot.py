"""
Telegram-бот: открывает Mini App, принимает результаты.
Запускается вместе с API-сервером в одном процессе (bot.py — точка входа).
"""

import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

import database as db
import api as api_module
from config import BOT_TOKEN, MINI_APP_URL, API_HOST, API_PORT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

router = Router()


# ── /start ────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📋 Открыть тестирование", web_app=WebAppInfo(url=MINI_APP_URL))
    ]])
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Здесь вы можете пройти тестирование по четырём направлениям:\n"
        "⚖️ Правовая подготовка\n"
        "🏛 Политическая подготовка\n"
        "🔫 Огневая подготовка\n"
        "🪖 Тактико-специальная подготовка\n\n"
        "Нажмите кнопку ниже, чтобы начать:",
        reply_markup=kb,
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📋 Открыть тестирование", web_app=WebAppInfo(url=MINI_APP_URL))
    ]])
    await message.answer(
        "📌 *Режимы тестирования*\n\n"
        "• *Один билет* — выберите направление и номер билета\n"
        "• *Все билеты* — пройдите все 50 вопросов направления\n"
        "• *Экзамен* — по одному случайному билету из каждого направления (4×5=20 вопросов)\n\n"
        "📊 История результатов доступна в приложении.",
        parse_mode="Markdown",
        reply_markup=kb,
    )


# ── Запуск ────────────────────────────────────

async def main():
    await db.create_pool()
    log.info("DB pool ready")

    bot = Bot(token=BOT_TOKEN)
    dp  = Dispatcher()
    dp.include_router(router)

    app = api_module.create_app()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, API_HOST, API_PORT)
    await site.start()
    log.info("API server started on %s:%s", API_HOST, API_PORT)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

    await runner.cleanup()
    await db.close_pool()


if __name__ == "__main__":
    asyncio.run(main())
