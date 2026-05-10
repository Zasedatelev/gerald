# 📋 Quiz Telegram Mini App

Система тестирования для 4 направлений подготовки с авторизацией, историей результатов и режимом «Экзамен».

## Структура

```
quiz_tma/
├── bot.py            # Точка входа (бот + API в одном процессе)
├── api.py            # REST API (aiohttp)
├── database.py       # Работа с PostgreSQL (asyncpg)
├── auth.py           # bcrypt + JWT
├── config.py         # Настройки (токен, URL, DB)
├── schema.sql        # Схема БД
├── seed_db.py        # Наполнение базы данных
├── requirements.txt
└── frontend/
    └── index.html    # Telegram Mini App (SPA)
```

---

## Быстрый старт

### 1. PostgreSQL

```bash
# Создайте базу данных
createdb quiz_tma

# Применить схему
psql quiz_tma < schema.sql
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка config.py

```python
BOT_TOKEN    = "123456:ABC..."         # токен от @BotFather
MINI_APP_URL = "https://your-site.com" # URL index.html (HTTPS!)
DATABASE_URL = "postgresql://user:pass@localhost:5432/quiz_tma"
JWT_SECRET   = "длинная-секретная-строка"
```

Или задайте через переменные окружения:
```bash
export BOT_TOKEN=...
export MINI_APP_URL=...
export DATABASE_URL=...
export JWT_SECRET=...
```

### 4. Заполнить базу данных

```bash
python seed_db.py
```

> ⚠️ В `seed_db.py` вставлены примерные вопросы. Замените их реальными в массивах `LEGAL_QUESTIONS`, `POLITICAL_QUESTIONS`, `FIRE_QUESTIONS`, `TACTICAL_QUESTIONS`.

### 5. Хостинг frontend/index.html

Mini App обязан быть доступен по HTTPS. Вариант для начала:
- **Nginx** на VPS: укажите `root /path/to/quiz_tma/frontend;`
- **Netlify Drop**: перетащите папку `frontend/` на [app.netlify.com/drop](https://app.netlify.com/drop)

В `frontend/index.html` проверьте строку:
```js
const API = window.location.origin;  // если фронт и API на одном хосте
// const API = 'https://api.example.com';  // или отдельный URL
```

### 6. Запуск

```bash
python bot.py
```

Бот и API запускаются в одном процессе. API слушает на `0.0.0.0:8080`.

---

## Архитектура

```
Пользователь → Telegram
    │
    ▼
Бот (aiogram) — показывает кнопку Web App
    │
    ▼
Mini App (index.html) — открывается в Telegram
    │  JWT-запросы
    ▼
REST API (aiohttp :8080)
    │
    ▼
PostgreSQL
```

---

## API эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/auth/register` | Регистрация (telegram_id + password) |
| POST | `/api/auth/login`    | Вход |
| GET  | `/api/directions`   | Список направлений |
| GET  | `/api/tickets/{slug}` | Билеты направления |
| GET  | `/api/questions/{ticket_id}` | Вопросы билета (перемешаны) |
| GET  | `/api/questions/all/{slug}`  | Все вопросы направления |
| GET  | `/api/random/{slug}`         | Случайный билет |
| POST | `/api/result`               | Сохранить результат |
| GET  | `/api/history`              | История пользователя |

---

## Режимы тестирования

| Режим | Описание |
|---|---|
| **Один билет** | Выбор направления → выбор номера билета (1–10) |
| **Случайный билет** | Случайный билет из выбранного направления |
| **Все билеты** | Все 50 вопросов направления подряд |
| **Экзамен** | По одному случайному билету из каждого из 4 направлений (20 вопросов) |

---

## Возможности

- ✅ Авторизация (telegram_id + пароль, bcrypt + JWT)
- ✅ 4 направления × 10 билетов × 5 вопросов
- ✅ Перемешивание вариантов ответов при каждом показе
- ✅ Мгновенная обратная связь (правильно/неверно)
- ✅ Подсветка правильного ответа
- ✅ Режим «Все вопросы направления»
- ✅ Режим «Экзамен» (4×5=20 вопросов)
- ✅ Сохранение результатов в PostgreSQL
- ✅ История тестирования (дата, направление, счёт)
- ✅ Адаптивный тёмный UI под Telegram
