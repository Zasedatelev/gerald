"""
REST API (aiohttp) для Telegram Mini App.

Эндпоинты:
  POST /api/auth/register   — регистрация
  POST /api/auth/login      — вход
  GET  /api/directions      — список направлений
  GET  /api/tickets/{dir}   — билеты направления
  GET  /api/questions/{ticket_id}  — вопросы билета (перемешанные)
  GET  /api/questions/all/{dir_slug} — все вопросы направления
  POST /api/result          — сохранить результат
  GET  /api/history         — история пользователя
"""

import json
import random

from aiohttp import web

import auth
import database as db

# ── Middleware: авторизация ────────────────────

@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        return web.Response(headers={
            "Access-Control-Allow-Origin":  "*",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        })
    resp = await handler(request)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return resp


def get_user_from_request(request: web.Request) -> dict | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[7:]
    return auth.decode_token(token)


def require_auth(handler):
    async def wrapper(request: web.Request):
        user = get_user_from_request(request)
        if not user:
            return err(401, "Unauthorized")
        request["user"] = user
        return await handler(request)
    return wrapper


# ── Helpers ───────────────────────────────────

def ok(data: dict | list) -> web.Response:
    return web.Response(
        text=json.dumps(data, ensure_ascii=False, default=str),
        content_type="application/json",
    )


def err(status: int, message: str) -> web.Response:
    return web.Response(
        status=status,
        text=json.dumps({"error": message}, ensure_ascii=False),
        content_type="application/json",
    )


def shuffle_answers(questions: list[dict]) -> list[dict]:
    """Перемешивает варианты ответов в каждом вопросе."""
    result = []
    for q in questions:
        answers = list(q["answers"])
        random.shuffle(answers)
        result.append({**q, "answers": answers})
    return result


# ── Auth ──────────────────────────────────────

async def register(request: web.Request) -> web.Response:
    body = await request.json()
    tg_id    = int(body.get("telegram_id", 0))
    password = body.get("password", "").strip()

    login_str = str(tg_id)
    if len(login_str) != 10 or not login_str.isdigit():
        return err(400, "Логин должен содержать ровно 10 цифр")
    if len(password) < 4:
        return err(400, "Пароль минимум 4 символа")

    existing = await db.get_user_by_tg(tg_id)
    if existing:
        return err(409, "Пользователь уже зарегистрирован")

    pw_hash = auth.hash_password(password)
    user_id = await db.create_user(tg_id, pw_hash)
    token, _ = auth.create_token(user_id, tg_id)

    return ok({"token": token, "user_id": user_id})


async def login(request: web.Request) -> web.Response:
    body = await request.json()
    tg_id    = int(body.get("telegram_id", 0))
    password = body.get("password", "").strip()

    user = await db.get_user_by_tg(tg_id)
    if not user or not auth.verify_password(password, user["password"]):
        return err(401, "Неверный ID или пароль")

    token, _ = auth.create_token(user["id"], tg_id)

    return ok({"token": token, "user_id": user["id"]})


# ── Directions ────────────────────────────────

@require_auth
async def get_directions(request: web.Request) -> web.Response:
    dirs = await db.get_directions()
    return ok([{"id": d["id"], "slug": d["slug"], "title": d["title"]} for d in dirs])


# ── Tickets ───────────────────────────────────

@require_auth
async def get_tickets(request: web.Request) -> web.Response:
    slug = request.match_info["slug"]
    d = await db.get_direction_by_slug(slug)
    if not d:
        return err(404, "Направление не найдено")
    tickets = await db.get_tickets_by_direction(d["id"])
    return ok([{"id": t["id"], "number": t["number"]} for t in tickets])


# ── Questions (single ticket) ─────────────────

@require_auth
async def get_questions(request: web.Request) -> web.Response:
    ticket_id = int(request.match_info["ticket_id"])
    questions = await db.get_ticket_questions(ticket_id)
    return ok(shuffle_answers(questions))


# ── Questions (all in direction) ──────────────

@require_auth
async def get_all_questions(request: web.Request) -> web.Response:
    slug = request.match_info["slug"]
    d = await db.get_direction_by_slug(slug)
    if not d:
        return err(404, "Направление не найдено")
    tickets_data = await db.get_all_tickets_questions(d["id"])
    # Перемешиваем ответы
    for td in tickets_data:
        td["questions"] = shuffle_answers(td["questions"])
    return ok(tickets_data)


# ── Random ticket (for exam mode) ────────────

@require_auth
async def get_random_ticket_questions(request: web.Request) -> web.Response:
    slug = request.match_info["slug"]
    d = await db.get_direction_by_slug(slug)
    if not d:
        return err(404, "Направление не найдено")
    ticket = await db.get_random_ticket(d["id"])
    questions = await db.get_ticket_questions(ticket["id"])
    return ok({
        "ticket_id":     ticket["id"],
        "ticket_number": ticket["number"],
        "direction_id":  d["id"],
        "direction_slug": slug,
        "questions":     shuffle_answers(questions),
    })


# ── Save result ───────────────────────────────

@require_auth
async def save_result(request: web.Request) -> web.Response:
    user  = request["user"]
    body  = await request.json()
    mode  = body.get("mode")          # 'ticket' | 'all' | 'exam'
    correct    = int(body.get("correct", 0))
    total      = int(body.get("total", 0))
    direction_id = body.get("direction_id")
    ticket_id    = body.get("ticket_id")

    if mode not in ("ticket", "all", "exam"):
        return err(400, "Неверный mode")

    rid = await db.save_result(
        user["sub"], direction_id, ticket_id, mode, correct, total
    )
    return ok({"result_id": rid})


# ── History ───────────────────────────────────

@require_auth
async def get_history(request: web.Request) -> web.Response:
    user = request["user"]
    rows = await db.get_history(user["sub"])
    return ok([dict(r) for r in rows])


# ── App factory ───────────────────────────────

def create_app() -> web.Application:
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_route("OPTIONS", "/{path_info:.*}", lambda r: web.Response())
    # Healthcheck — Amvera проверяет доступность сервиса
    app.router.add_get("/",                           lambda r: web.Response(text="ok"))
    app.router.add_post("/api/auth/register",         register)
    app.router.add_post("/api/auth/login",            login)
    app.router.add_get ("/api/directions",            get_directions)
    app.router.add_get ("/api/tickets/{slug}",        get_tickets)
    # /all/{slug} ОБЯЗАТЕЛЬНО перед /{ticket_id} — иначе aiohttp матчит "all" как ticket_id
    app.router.add_get ("/api/questions/all/{slug}",  get_all_questions)
    app.router.add_get ("/api/questions/{ticket_id}", get_questions)
    app.router.add_get ("/api/random/{slug}",         get_random_ticket_questions)
    app.router.add_post("/api/result",                save_result)
    app.router.add_get ("/api/history",               get_history)
    # ── Срезы ────────────────────────────────────
    app.router.add_post("/api/slices",                     create_slice)
    app.router.add_get ("/api/slices/my",                  my_slices)
    app.router.add_get ("/api/slices/{slice_id}",          slice_info)
    app.router.add_post("/api/slices/{slice_id}/join",     join_slice)
    app.router.add_post("/api/slices/{slice_id}/submit",   submit_slice)
    app.router.add_get ("/api/slices/{slice_id}/results",  slice_results)

    return app


# ══════════════════════════════════════════════════════════════
#  СРЕЗЫ
# ══════════════════════════════════════════════════════════════

import datetime as dt

# ── Создать срез ──────────────────────────────

@require_auth
async def create_slice(request: web.Request) -> web.Response:
    user = request["user"]
    body = await request.json()

    title        = body.get("title", "").strip()
    password     = body.get("password", "").strip()
    direction_id = body.get("direction_id")   # None для геральдики (exam-режим)
    slice_type   = body.get("slice_type", "single")  # "single" | "heraldry" | "coming_soon"
    pass_percent = int(body.get("pass_percent", 60))
    duration_min = int(body.get("duration_min", 30))

    if not title or not password:
        return err(400, "title и password обязательны")
    if slice_type == "single" and not direction_id:
        return err(400, "direction_id обязателен для одиночного направления")
    if duration_min < 1 or duration_min > 180:
        return err(400, "Длительность от 1 до 180 минут")

    ends_at = dt.datetime.utcnow() + dt.timedelta(minutes=duration_min)

    pool = await db.get_pool()
    slice_id = await pool.fetchval("""
        INSERT INTO slices (admin_id, direction_id, title, password, pass_percent, duration_min, ends_at, slice_type)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id
    """, user["sub"], direction_id, title, password, pass_percent, duration_min, ends_at, slice_type)

    return ok({"slice_id": slice_id, "ends_at": ends_at.strftime("%Y-%m-%dT%H:%M:%SZ")})


# ── Войти в срез ─────────────────────────────

@require_auth
async def join_slice(request: web.Request) -> web.Response:
    user    = request["user"]
    slice_id = int(request.match_info["slice_id"])
    body    = await request.json()
    password = body.get("password", "").strip()

    pool = await db.get_pool()
    slc  = await pool.fetchrow("SELECT * FROM slices WHERE id=$1", slice_id)
    if not slc:
        return err(404, "Срез не найден")
    if slc["password"] != password:
        return err(403, "Неверный пароль")
    if dt.datetime.utcnow() > slc["ends_at"].replace(tzinfo=None):
        return err(410, "Срез уже завершён")

    # Уже участвует?
    existing = await pool.fetchrow(
        "SELECT * FROM slice_participants WHERE slice_id=$1 AND user_id=$2",
        slice_id, user["sub"]
    )
    if existing:
        # Возвращаем уже выданный билет
        qs = await db.get_ticket_questions(existing["ticket_id"])
        return ok({
            "participant_id": existing["id"],
            "ticket_id":      existing["ticket_id"],
            "ends_at":        slc["ends_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_min":   slc["duration_min"],
            "questions":      shuffle_answers(qs),
        })

    slice_type = slc.get("slice_type", "single")

    if slice_type == "coming_soon":
        return err(400, "Этот раздел пока недоступен")

    if slice_type == "heraldry":
        # Как режим Экзамен — по одному случайному билету из каждого направления
        dirs = await pool.fetch("SELECT id, title FROM directions ORDER BY id")
        all_questions = []
        tickets_info = []   # [{direction_title, ticket_number}]
        first_ticket_id = None
        for d in dirs:
            t = await db.get_random_ticket(d["id"])
            if t:
                if first_ticket_id is None:
                    first_ticket_id = t["id"]
                tickets_info.append({
                    "direction_title": d["title"],
                    "ticket_number":   t["number"],
                    "ticket_id":       t["id"],
                })
                qs = await db.get_ticket_questions(t["id"])
                # Добавляем мета-данные к вопросам для результата
                for q in qs:
                    q["direction_title"] = d["title"]
                    q["ticket_number"]   = t["number"]
                all_questions.extend(qs)

        pid = await pool.fetchval("""
            INSERT INTO slice_participants (slice_id, user_id, ticket_id)
            VALUES ($1,$2,$3) RETURNING id
        """, slice_id, user["sub"], first_ticket_id)

        import json as _json
        # Сохраняем список всех билетов в отдельную запись
        await pool.execute("""
            UPDATE slice_participants SET tickets_json=$1 WHERE id=$2
        """, _json.dumps(tickets_info, ensure_ascii=False), pid)

        return ok({
            "participant_id": pid,
            "tickets_info":   tickets_info,
            "ends_at":        slc["ends_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_min":   slc["duration_min"],
            "questions":      shuffle_answers(all_questions),
            "slice_type":     "heraldry",
        })

    # single — случайный билет из одного направления
    ticket = await db.get_random_ticket(slc["direction_id"])
    if not ticket:
        return err(500, "Нет билетов для этого направления")

    pid = await pool.fetchval("""
        INSERT INTO slice_participants (slice_id, user_id, ticket_id)
        VALUES ($1,$2,$3) RETURNING id
    """, slice_id, user["sub"], ticket["id"])

    qs = await db.get_ticket_questions(ticket["id"])
    return ok({
        "participant_id": pid,
        "ticket_id":      ticket["id"],
        "ends_at":        slc["ends_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_min":   slc["duration_min"],
        "questions":      shuffle_answers(qs),
        "slice_type":     "single",
    })


# ── Сохранить ответы участника ────────────────

@require_auth
async def submit_slice(request: web.Request) -> web.Response:
    user    = request["user"]
    slice_id = int(request.match_info["slice_id"])
    body    = await request.json()
    # answers: [{question_id, answer_id}]  answer_id=null если не ответил
    answers  = body.get("answers", [])

    pool = await db.get_pool()
    slc  = await pool.fetchrow("SELECT * FROM slices WHERE id=$1", slice_id)
    if not slc:
        return err(404, "Срез не найден")

    part = await pool.fetchrow(
        "SELECT * FROM slice_participants WHERE slice_id=$1 AND user_id=$2",
        slice_id, user["sub"]
    )
    if not part:
        return err(403, "Вы не участник этого среза")

    correct = 0
    total   = 0

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Удаляем старые ответы если повторная отправка
            await conn.execute(
                "DELETE FROM slice_answers WHERE participant_id=$1", part["id"]
            )
            for a in answers:
                q_id   = a.get("question_id")
                ans_id = a.get("answer_id")
                is_cor = False
                if ans_id:
                    is_cor = await conn.fetchval(
                        "SELECT is_correct FROM answers WHERE id=$1", ans_id
                    ) or False
                if is_cor:
                    correct += 1
                total += 1
                await conn.execute("""
                    INSERT INTO slice_answers (participant_id, question_id, answer_id, is_correct)
                    VALUES ($1,$2,$3,$4)
                """, part["id"], q_id, ans_id, is_cor)

            await conn.execute("""
                UPDATE slice_participants
                SET correct=$1, total=$2, finished_at=NOW()
                WHERE id=$3
            """, correct, total, part["id"])

    return ok({"correct": correct, "total": total})


# ── Результаты среза (для админа) ─────────────

@require_auth
async def slice_results(request: web.Request) -> web.Response:
    user     = request["user"]
    slice_id = int(request.match_info["slice_id"])

    pool = await db.get_pool()
    slc  = await pool.fetchrow("SELECT * FROM slices WHERE id=$1", slice_id)
    if not slc:
        return err(404, "Срез не найден")
    if slc["admin_id"] != user["sub"]:
        return err(403, "Только админ может смотреть результаты")

    participants = await pool.fetch("""
        SELECT sp.id, sp.user_id, sp.ticket_id, sp.correct, sp.total,
               sp.started_at, sp.finished_at,
               sp.tickets_json,
               u.telegram_id,
               t.number AS ticket_number,
               d.title  AS direction_title
        FROM slice_participants sp
        JOIN users u   ON u.id  = sp.user_id
        LEFT JOIN tickets    t ON t.id = sp.ticket_id
        LEFT JOIN directions d ON d.id = t.direction_id
        WHERE sp.slice_id = $1
        ORDER BY sp.finished_at NULLS LAST
    """, slice_id)

    results = []
    for p in participants:
        # Неправильные ответы
        wrong_answers = await pool.fetch("""
            SELECT q.text AS question_text, a.text AS answer_text
            FROM slice_answers sa
            JOIN questions q ON q.id = sa.question_id
            LEFT JOIN answers a ON a.id = sa.answer_id
            WHERE sa.participant_id=$1 AND sa.is_correct=false
        """, p["id"])

        pct    = round(p["correct"] / p["total"] * 100) if p["total"] else 0
        passed = pct >= slc["pass_percent"]

        # Для геральдики берём список всех билетов из JSON
        import json as _json
        tickets_info = []
        if p["tickets_json"]:
            try:
                tickets_info = _json.loads(p["tickets_json"])
            except Exception:
                pass

        # Формируем строку с билетами для отображения
        if tickets_info:
            tickets_str = ", ".join(
                f"{t['direction_title']} (билет {t['ticket_number']})"
                for t in tickets_info
            )
        else:
            dir_title = p["direction_title"] or "—"
            tkt_num   = p["ticket_number"] or "—"
            tickets_str = f"{dir_title} (билет {tkt_num})"

        results.append({
            "user_login":    str(p["telegram_id"]),
            "tickets_str":   tickets_str,
            "tickets_info":  tickets_info,
            "correct":       p["correct"],
            "total":         p["total"],
            "percent":       pct,
            "passed":        passed,
            "grade":         "Зачёт" if passed else "Незачёт",
            "finished":      bool(p["finished_at"]),
            "wrong_answers": [dict(w) for w in wrong_answers],
        })

    return ok({
        "slice_id":    slice_id,
        "title":       slc["title"],
        "ends_at":     slc["ends_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pass_percent": slc["pass_percent"],
        "participants": results,
    })


# ── Мои срезы (созданные) ─────────────────────

@require_auth
async def my_slices(request: web.Request) -> web.Response:
    user = request["user"]
    pool = await db.get_pool()
    rows = await pool.fetch("""
        SELECT s.id, s.title, s.ends_at, s.pass_percent, s.duration_min,
               s.slice_type,
               d.title AS direction_title,
               COUNT(sp.id) AS participant_count
        FROM slices s
        LEFT JOIN directions d ON d.id = s.direction_id
        LEFT JOIN slice_participants sp ON sp.slice_id = s.id
        WHERE s.admin_id = $1
        GROUP BY s.id, d.title
        ORDER BY s.created_at DESC
    """, user["sub"])
    return ok([dict(r) for r in rows])


# ── Инфо о срезе по ID (для участника) ───────

async def slice_info(request: web.Request) -> web.Response:
    slice_id = int(request.match_info["slice_id"])
    pool = await db.get_pool()
    slc  = await pool.fetchrow("""
        SELECT s.id, s.title, s.ends_at, s.pass_percent, s.duration_min,
               d.title AS direction_title
        FROM slices s
        LEFT JOIN directions d ON d.id = s.direction_id
        WHERE s.id = $1
    """, slice_id)
    if not slc:
        return err(404, "Срез не найден")
    now = dt.datetime.utcnow()
    return ok({**dict(slc), "is_active": now < slc["ends_at"].replace(tzinfo=None)})