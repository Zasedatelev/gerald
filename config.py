"""
Конфигурация приложения.
Значения читаются из переменных окружения или заданы напрямую.
"""

import os

# ── Бот ──────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ── URL Mini App (HTTPS!) ─────────────────────
MINI_APP_URL = os.getenv("MINI_APP_URL")
    
# ── PostgreSQL ────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

# ── JWT ──────────────────────────────────────
JWT_SECRET  = os.getenv("JWT_SECRET", "change_me_in_production_very_long_secret")
JWT_EXPIRES = int(os.getenv("JWT_EXPIRES_HOURS", "24"))   # часов

# ── API-сервер (aiohttp) ──────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ── Настройки теста ───────────────────────────
PASS_PERCENT = 100  # проходной балл в процентах
