"""
Аутентификация: bcrypt для паролей, JWT для сессий Mini App.
"""

import datetime
import jwt
import bcrypt

from config import JWT_SECRET, JWT_EXPIRES


# ── Пароли ────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ───────────────────────────────────────

def create_token(user_id: int, telegram_id: int) -> tuple[str, datetime.datetime]:
    expires = datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRES)
    payload = {
        "sub": user_id,
        "tg":  telegram_id,
        "exp": expires,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token, expires


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
