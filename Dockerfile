# ════════════════════════════════════════════════
#  Dockerfile — Quiz Telegram Mini App
#  Один контейнер: aiogram-бот + aiohttp REST API
#
#  Сборка:
#    docker build -t quiz-tma .
#
#  Запуск (локально):
#    docker run -d \
#      -e BOT_TOKEN=123:ABC \
#      -e DATABASE_URL=postgresql://user:pass@host:5432/db \
#      -e MINI_APP_URL=https://your-vercel.app \
#      -e JWT_SECRET=very_long_secret \
#      -p 8000:8000 \
#      quiz-tma
# ════════════════════════════════════════════════

# ── Stage 1: сборка зависимостей ─────────────────
FROM python:3.11-slim AS deps

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc \
      libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: финальный образ ─────────────────────
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копируем пакеты из stage 1
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Исходники
COPY bot.py api.py database.py auth.py config.py ./
COPY frontend/ ./frontend/

# Переменные окружения (переопределяйте через -e или docker-compose)
ENV BOT_TOKEN=""
ENV DATABASE_URL=""
ENV MINI_APP_URL=""
ENV JWT_SECRET="change_me_in_production"
ENV JWT_EXPIRES_HOURS="24"
ENV API_HOST="0.0.0.0"
ENV API_PORT="8000"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["python", "bot.py"]
