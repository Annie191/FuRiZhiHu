from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: Any = None):
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def error_response(error: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status,
        content={"error": {"code": error.code, "message": error.message, "details": error.details}},
    )


def validation_details(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    for error in errors:
        location = [str(part) for part in error["loc"] if part not in {"body", "query", "path"}]
        details.append({"path": ".".join(location), "message": error["msg"]})
    return details


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, error: ApiError) -> JSONResponse:
        return error_response(error)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        return error_response(ApiError(400, "VALIDATION_ERROR", "Request validation failed.", validation_details(error.errors())))

    @app.exception_handler(sqlite3.IntegrityError)
    async def handle_integrity_error(_: Request, error: sqlite3.IntegrityError) -> JSONResponse:
        message = str(error).upper()
        if "UNIQUE" in message or "PRIMARY KEY" in message:
            return error_response(ApiError(409, "CONFLICT", "The submitted data conflicts with an existing record."))
        return error_response(ApiError(400, "VALIDATION_ERROR", "The submitted data violates a database constraint."))

    @app.exception_handler(sqlite3.Error)
    async def handle_database_error(_: Request, __: sqlite3.Error) -> JSONResponse:
        return error_response(ApiError(500, "INTERNAL_ERROR", "An unexpected error occurred."))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        if error.status_code == 404:
            return error_response(ApiError(404, "RESOURCE_NOT_FOUND", f"Route {request.method} {request.url.path} was not found."))
        return error_response(ApiError(error.status_code, "INTERNAL_ERROR", "An unexpected error occurred."))
