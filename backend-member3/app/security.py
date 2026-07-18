from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .errors import ApiError

DUMMY_HASH = b"$2b$12$FBCJFKLkwjQw3lBcPTsO7u4KhVyrpXzoWx8ck2fCeumBGSj/CfT6q"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def password_matches(password: str, password_hash: str | bytes) -> bool:
    encoded_hash = password_hash.encode() if isinstance(password_hash, str) else password_hash
    return bcrypt.checkpw(password.encode(), encoded_hash)


def parse_expiry(value: str) -> timedelta:
    amount, unit = int(value[:-1]), value[-1]
    return timedelta(**{"s": {"seconds": amount}, "m": {"minutes": amount}, "h": {"hours": amount}, "d": {"days": amount}, "w": {"weeks": amount}}[unit])


def sign_token(user_id: int, username: str, secret: str, expires_in: str) -> str:
    payload = {"sub": str(user_id), "username": username, "exp": datetime.now(timezone.utc) + parse_expiry(expires_in)}
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_token(token: str, secret: str) -> tuple[int, str]:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["sub", "username", "exp"]})
        user_id = int(payload["sub"])
        username = payload["username"]
        if user_id <= 0 or not isinstance(username, str):
            raise ValueError("Invalid token payload.")
        return user_id, username
    except (jwt.PyJWTError, ValueError, TypeError) as error:
        raise ApiError(401, "INVALID_TOKEN", "Authentication token is invalid.") from error
