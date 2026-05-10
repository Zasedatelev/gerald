"""
Работа с PostgreSQL через asyncpg.
"""

import asyncpg
from config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def create_pool():
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)


async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Pool not initialised")
    return _pool


async def close_pool():
    if _pool:
        await _pool.close()


# ── Пользователи ──────────────────────────────

async def get_user_by_tg(telegram_id: int) -> asyncpg.Record | None:
    pool = await get_pool()
    return await pool.fetchrow("SELECT * FROM users WHERE telegram_id=$1", telegram_id)


async def create_user(telegram_id: int, password_hash: str) -> int:
    pool = await get_pool()
    return await pool.fetchval(
        "INSERT INTO users(telegram_id, password) VALUES($1,$2) RETURNING id",
        telegram_id, password_hash,
    )


# ── Сессии ────────────────────────────────────

async def save_session(user_id: int, token: str, expires_at):
    pool = await get_pool()
    await pool.execute(
        "INSERT INTO sessions(user_id, token, expires_at) VALUES($1,$2,$3) "
        "ON CONFLICT(token) DO NOTHING",
        user_id, token, expires_at,
    )


async def get_session(token: str) -> asyncpg.Record | None:
    pool = await get_pool()
    return await pool.fetchrow(
        "SELECT s.*, u.telegram_id FROM sessions s "
        "JOIN users u ON u.id = s.user_id "
        "WHERE s.token=$1 AND s.expires_at > NOW()",
        token,
    )


# ── Направления ───────────────────────────────

async def get_directions() -> list[asyncpg.Record]:
    pool = await get_pool()
    return await pool.fetch("SELECT * FROM directions ORDER BY id")


async def get_direction_by_slug(slug: str) -> asyncpg.Record | None:
    pool = await get_pool()
    return await pool.fetchrow("SELECT * FROM directions WHERE slug=$1", slug)


# ── Билеты ────────────────────────────────────

async def get_tickets_by_direction(direction_id: int) -> list[asyncpg.Record]:
    pool = await get_pool()
    return await pool.fetch(
        "SELECT * FROM tickets WHERE direction_id=$1 ORDER BY number",
        direction_id,
    )


async def get_random_ticket(direction_id: int) -> asyncpg.Record | None:
    pool = await get_pool()
    return await pool.fetchrow(
        "SELECT * FROM tickets WHERE direction_id=$1 ORDER BY RANDOM() LIMIT 1",
        direction_id,
    )


# ── Вопросы + ответы ──────────────────────────

async def get_ticket_questions(ticket_id: int) -> list[dict]:
    """Возвращает вопросы билета вместе со списком ответов."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT q.id   AS q_id,
               q.position,
               q.text AS q_text,
               a.id   AS a_id,
               a.text AS a_text,
               a.is_correct
        FROM questions q
        JOIN answers a ON a.question_id = q.id
        WHERE q.ticket_id = $1
        ORDER BY q.position, a.id
        """,
        ticket_id,
    )

    questions: dict[int, dict] = {}
    for r in rows:
        if r["q_id"] not in questions:
            questions[r["q_id"]] = {
                "id": r["q_id"],
                "position": r["position"],
                "text": r["q_text"],
                "answers": [],
            }
        questions[r["q_id"]]["answers"].append({
            "id": r["a_id"],
            "text": r["a_text"],
            "is_correct": r["is_correct"],
        })

    return list(questions.values())


async def get_all_tickets_questions(direction_id: int) -> list[dict]:
    """Все вопросы направления, сгруппированные по билетам."""
    pool = await get_pool()
    tickets = await get_tickets_by_direction(direction_id)
    result = []
    for t in tickets:
        qs = await get_ticket_questions(t["id"])
        result.append({"ticket_id": t["id"], "ticket_number": t["number"], "questions": qs})
    return result


# ── Результаты ────────────────────────────────

async def save_result(
    user_id: int,
    direction_id: int | None,
    ticket_id: int | None,
    mode: str,
    correct: int,
    total: int,
) -> int:
    pool = await get_pool()
    return await pool.fetchval(
        """INSERT INTO results(user_id, direction_id, ticket_id, mode, correct, total)
           VALUES($1,$2,$3,$4,$5,$6) RETURNING id""",
        user_id, direction_id, ticket_id, mode, correct, total,
    )


async def get_history(user_id: int) -> list[asyncpg.Record]:
    pool = await get_pool()
    return await pool.fetch(
        """
        SELECT r.finished_at,
               r.mode,
               r.correct,
               r.total,
               d.title AS direction_title,
               d.slug  AS direction_slug,
               t.number AS ticket_number
        FROM results r
        LEFT JOIN directions d ON d.id = r.direction_id
        LEFT JOIN tickets    t ON t.id = r.ticket_id
        WHERE r.user_id = $1
        ORDER BY r.finished_at DESC
        LIMIT 100
        """,
        user_id,
    )
