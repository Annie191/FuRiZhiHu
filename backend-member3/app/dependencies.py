from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import Depends, Header

from .config import Settings
from .db import database_dependency
from .errors import ApiError
from .security import verify_token


def make_dependencies(settings: Settings):
    get_db = database_dependency(settings.resolved_database_path)

    def current_principal(
        authorization: Annotated[str | None, Header()] = None,
        connection: sqlite3.Connection = Depends(get_db),
    ) -> dict[str, int | str]:
        if not authorization or not authorization.startswith("Bearer ") or not authorization[7:].strip():
            raise ApiError(401, "AUTH_REQUIRED", "Authentication token is required.")
        user_id, username = verify_token(authorization[7:].strip(), settings.jwt_secret)
        principal = connection.execute(
            "SELECT user_id, username FROM user_account WHERE user_id = ? AND status = 1", (user_id,)
        ).fetchone()
        if not principal or principal["username"] != username:
            raise ApiError(401, "INVALID_TOKEN", "Authentication token is invalid.")
        return {"user_id": user_id, "username": username}

    return get_db, current_principal
