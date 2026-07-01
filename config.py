"""
Конфигурация приложения.
Все значения берутся из переменных окружения.
На Amvera задаются в разделе «Переменные» проекта.
"""
import os

# ── Бот ──────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ── URL фронтенда на Amvera (HTTPS) ──────────
MINI_APP_URL = os.getenv("MINI_APP_URL", "")

# ── PostgreSQL (Amvera даёт строку вида ниже) ─
DATABASE_URL = os.getenv("DATABASE_URL", "")

# ── JWT ──────────────────────────────────────
JWT_SECRET  = os.getenv("JWT_SECRET", "change_me_in_production_very_long_secret")
JWT_EXPIRES = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

# ── API-сервер ────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))  # Amvera пробрасывает PORT

# ── Настройки теста ───────────────────────────
PASS_PERCENT = int(os.getenv("PASS_PERCENT", "100"))
