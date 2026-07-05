"""
Конфигурация приложения.
"""
import os

# ── Бот ──────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ── URL фронтенда (Vercel) ────────────────────
MINI_APP_URL = os.getenv("MINI_APP_URL", "")

# ── PostgreSQL ────────────────────────────────
# Amvera даёт только hostname — без пароля и порта.
# Подключение через отдельные параметры, не через DSN.
DB_HOST = os.getenv("DB_HOST", "amvera-olegz2026-cnpg-testapp-bd-rw")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "olegzasedatelev")
DB_NAME = os.getenv("DB_NAME", "olegzasedatelev")
DB_PASS = os.getenv("DB_PASS", "")  # пустой пароль — Amvera использует peer/trust внутри

# DATABASE_URL оставляем для совместимости — собираем из частей если не задан
_dsn = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL = os.getenv("DATABASE_URL", _dsn)

# ── JWT ──────────────────────────────────────
JWT_SECRET  = os.getenv("JWT_SECRET", "change_me_in_production_very_long_secret")
JWT_EXPIRES = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

# ── API-сервер ────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))

# ── Настройки теста ───────────────────────────
PASS_PERCENT = int(os.getenv("PASS_PERCENT", "100"))
