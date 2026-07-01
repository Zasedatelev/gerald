# Деплой на Amvera из GitHub

Один репозиторий GitHub → два проекта на Amvera.

## Структура репозитория

```
gerald/                   ← корень репо (бэкенд-проект на Amvera)
├── Dockerfile            ← бэкенд
├── amvera.yml            ← конфиг бэкенда
├── bot.py
├── api.py
├── database.py
├── auth.py
├── config.py
├── requirements.txt
├── schema.sql
├── seed_db.py
└── frontend/             ← фронтенд-проект на Amvera
    ├── Dockerfile        ← nginx раздаёт index.html
    ├── amvera.yml        ← конфиг фронтенда
    └── index.html
```

---

## Шаг 1 — PostgreSQL

1. Amvera → **Создать проект** → тип **PostgreSQL** → имя `quiz-db`
2. Проект → **Подключение** → скопируйте `DATABASE_URL`:
   ```
   postgresql://USER:PASS@quiz-db-ВАШ_ЛОГИН.db-msk0.amvera.tech:5432/USER
   ```
3. Примените схему:
   ```bash
   psql "postgresql://USER:PASS@quiz-db-ВАШ_ЛОГИН.db-msk0.amvera.tech:5432/USER" -f schema.sql
   ```

---

## Шаг 2 — Бэкенд-проект

1. Amvera → **Создать проект** → тип **Docker** → имя `quiz-backend`
2. **Источник кода** → GitHub → выбрать репозиторий `gerald`
3. **Ветка**: `main`
4. **Dockerfile**: `Dockerfile` (в корне — подхватится автоматически)

### Переменные окружения (Проект → Переменные)

| Переменная | Значение |
|---|---|
| `BOT_TOKEN` | токен от @BotFather |
| `DATABASE_URL` | строка из шага 1 |
| `MINI_APP_URL` | URL фронтенда (заполните после шага 3) |
| `JWT_SECRET` | длинная случайная строка |
| `PASS_PERCENT` | 100 |

### URL бэкенда
```
https://quiz-backend-ВАШ_ЛОГИН.amvera.io
```

---

## Шаг 3 — Фронтенд-проект

### Сначала: прописать URL бэкенда в index.html
Откройте `frontend/index.html`, замените:
```js
const API = 'https://BACKEND_PROJECT.amvera.io';
// на:
const API = 'https://quiz-backend-ВАШ_ЛОГИН.amvera.io';
```
Закоммитьте и запушьте в GitHub.

### Создать проект
1. Amvera → **Создать проект** → тип **Docker** → имя `quiz-frontend`
2. **Источник кода** → GitHub → тот же репозиторий `gerald`
3. **Ветка**: `main`
4. **Dockerfile**: `frontend/Dockerfile`

### URL фронтенда
```
https://quiz-frontend-ВАШ_ЛОГИН.amvera.io
```

---

## Шаг 4 — Финал

В переменных бэкенда обновите:
```
MINI_APP_URL = https://quiz-frontend-ВАШ_ЛОГИН.amvera.io
```
Нажмите **Пересобрать** в проекте бэкенда.

В @BotFather → **Menu Button** → укажите URL фронтенда.

---

## При обновлении кода

Amvera автоматически пересобирает проект при каждом `git push` в GitHub.
```bash
git add .
git commit -m "update"
git push origin main
```
Оба проекта (бэкенд и фронтенд) пересоберутся автоматически.
