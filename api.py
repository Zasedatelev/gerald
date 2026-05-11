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
import os


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

    if not tg_id or len(password) < 4:
        return err(400, "telegram_id и пароль (мин. 4 символа) обязательны")

    existing = await db.get_user_by_tg(tg_id)
    if existing:
        return err(409, "Пользователь уже зарегистрирован")

    pw_hash = auth.hash_password(password)
    user_id = await db.create_user(tg_id, pw_hash)
    token, expires = auth.create_token(user_id, tg_id)
    await db.save_session(user_id, token, expires)

    return ok({"token": token, "user_id": user_id})


async def login(request: web.Request) -> web.Response:
    body = await request.json()
    tg_id    = int(body.get("telegram_id", 0))
    password = body.get("password", "").strip()

    user = await db.get_user_by_tg(tg_id)
    if not user or not auth.verify_password(password, user["password"]):
        return err(401, "Неверный ID или пароль")

    token, expires = auth.create_token(user["id"], tg_id)
    await db.save_session(user["id"], token, expires)

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
    app.router.add_post("/api/auth/register",         register)
    app.router.add_post("/api/auth/login",            login)
    app.router.add_get ("/api/directions",            get_directions)
    app.router.add_get ("/api/tickets/{slug}",        get_tickets)
    app.router.add_get ("/api/questions/{ticket_id}", get_questions)
    app.router.add_get ("/api/questions/all/{slug}",  get_all_questions)
    app.router.add_get ("/api/random/{slug}",         get_random_ticket_questions)
    app.router.add_post("/api/result",                save_result)
    app.router.add_get ("/api/history",               get_history)

    # Раздаём frontend/index.html по корню
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

    app.router.add_prefix("/api")
    return app
