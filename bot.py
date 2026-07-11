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
    # ── Лог переменных при старте ──
    log.info("✅ BOT_TOKEN = %s...", BOT_TOKEN[:6] if BOT_TOKEN else "НЕ ЗАДАН")
    log.info("✅ MINI_APP_URL = %s", MINI_APP_URL or "НЕ ЗАДАН")
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")

    await db.create_pool()
    log.info("DB pool ready")

    # ── Автоматическое применение схемы БД ──
    import pathlib
    schema_file = pathlib.Path("/app/schema.sql")
    if schema_file.exists():
        pool = await db.get_pool()
        sql = schema_file.read_text()
        try:
            await pool.execute(sql)
            log.info("✅ Схема БД применена")
        except Exception as e:
            log.warning("Схема уже применена или ошибка: %s", e)

    # ── Применяем миграции по одной таблице ──
    import pathlib
    pool = await db.get_pool()
    migrations = [
        ("slices",             "CREATE TABLE IF NOT EXISTS slices (id SERIAL PRIMARY KEY, admin_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, direction_id INTEGER REFERENCES directions(id) ON DELETE SET NULL, title VARCHAR(256) NOT NULL, password VARCHAR(256) NOT NULL, pass_percent SMALLINT NOT NULL DEFAULT 60, duration_min SMALLINT NOT NULL DEFAULT 30, ends_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"),
        ("slice_participants", "CREATE TABLE IF NOT EXISTS slice_participants (id SERIAL PRIMARY KEY, slice_id INTEGER NOT NULL REFERENCES slices(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, ticket_id INTEGER REFERENCES tickets(id) ON DELETE SET NULL, started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), finished_at TIMESTAMPTZ, correct SMALLINT, total SMALLINT, UNIQUE (slice_id, user_id))"),
        ("slice_answers",      "CREATE TABLE IF NOT EXISTS slice_answers (id SERIAL PRIMARY KEY, participant_id INTEGER NOT NULL REFERENCES slice_participants(id) ON DELETE CASCADE, question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE, answer_id INTEGER REFERENCES answers(id) ON DELETE SET NULL, is_correct BOOLEAN NOT NULL DEFAULT FALSE, answered_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"),
    ]
    for table_name, ddl in migrations:
        try:
            await pool.execute(ddl)
            log.info("✅ Таблица %s готова", table_name)
        except Exception as e:
            log.warning("Таблица %s: %s", table_name, e)

    # ── Миграция: tickets_json колонка ──
    try:
        await pool.execute("ALTER TABLE slice_participants ADD COLUMN IF NOT EXISTS tickets_json TEXT")
        log.info("✅ Колонка tickets_json готова")
    except Exception as e:
        log.warning("tickets_json: %s", e)

    # ── Миграция: slice_type колонка ──
    try:
        await pool.execute("ALTER TABLE slices ADD COLUMN IF NOT EXISTS slice_type VARCHAR(32) NOT NULL DEFAULT 'single'")
        log.info("✅ Колонка slice_type готова")
    except Exception as e:
        log.warning("slice_type: %s", e)

    # ── Автозаполнение направлений ──
    pool = await db.get_pool()
    count = await pool.fetchval("SELECT COUNT(*) FROM directions")
    if count == 0:
        await pool.execute("""
            INSERT INTO directions (slug, title) VALUES
            ('legal',     'Правовая подготовка'),
            ('political', 'Политическая подготовка'),
            ('fire',      'Огневая подготовка'),
            ('tactical',  'Тактико-специальная подготовка')
        """)
        log.info("✅ Направления добавлены в БД")
    else:
        log.info("✅ Направления уже есть в БД (%d шт.)", count)

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