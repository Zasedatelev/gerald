
# ════════════════════════════════════════════════
#  Dockerfile — бэкенд (bot.py + api.py)
#  Amvera читает этот файл из корня репозитория
# ════════════════════════════════════════════════
 
FROM python:3.11-slim
 
WORKDIR /app
 
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
 
COPY bot.py api.py database.py auth.py config.py ./
 
# Значения по умолчанию — переопределяются через переменные Amvera
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
# Внутренний хост БД Amvera — используется если DATABASE_URL не задан явно
ENV DATABASE_URL=postgresql://olegzasedatelev@amvera-olegz2026-cnpg-testapp-bd-rw/olegzasedatelev
 
EXPOSE 8000
 
CMD ["python", "bot.py"]
