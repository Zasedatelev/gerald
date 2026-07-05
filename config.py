"""
Конфигурация приложения.
"""
import os

# ── Бот ──────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "8740049939:AAGNWwk7CrFYUqP6tHipuRW-ZzlofBMCvdw")

# ── URL фронтенда (Vercel) ────────────────────
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://frontend-one-ochre-80.vercel.app")

# ── PostgreSQL ────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "amvera-olegz2026-cnpg-testapp-bd-rw")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_NAME = os.getenv("DB_NAME", "testAppbd")
DB_PASS = os.getenv("DB_PASS", "260616")

_dsn = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL = os.getenv("DATABASE_URL", _dsn)

# ── JWT ──────────────────────────────────────
JWT_SECRET  = os.getenv("JWT_SECRET", "change_me_in_production_very_long_secret")
JWT_EXPIRES = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

# ── API-сервер ────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))

# ── Настройки теста ───────────────────────────
PASS_PERCENT = int(os.getenv("PASS_PERCENT", "100"))
