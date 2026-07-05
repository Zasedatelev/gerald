FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY bot.py api.py database.py auth.py config.py ./

ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV DB_HOST=amvera-olegz2026-cnpg-testapp-bd-rw
ENV DB_PORT=5432
ENV DB_USER=postgres
ENV DB_NAME=testAppbd
ENV DB_PASS=260616

EXPOSE 8000

CMD ["python", "bot.py"]
