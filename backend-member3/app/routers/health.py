from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..dependencies import make_dependencies
from ..errors import ApiError


def router(settings) -> APIRouter:
    routes = APIRouter(tags=["health"])
    get_db, _ = make_dependencies(settings)

    @routes.get("/health")
    def health(connection: sqlite3.Connection = Depends(get_db)):
        try:
            connection.execute("SELECT 1").fetchone()
        except sqlite3.Error as error:
            raise ApiError(503, "SERVICE_UNAVAILABLE", "Database is unavailable.") from error
        return {"status": "ok", "service": "fucare-api", "database": "ok"}

    return routes
