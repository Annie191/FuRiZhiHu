from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..config import Settings
from ..dependencies import make_dependencies
from ..errors import ApiError
from ..repositories.auth import create_user, find_credential, format_user, public_user
from ..schemas.auth import LoginInput, RegistrationInput
from ..security import DUMMY_HASH, password_matches, sign_token


def router(settings: Settings) -> APIRouter:
    routes = APIRouter(prefix="/auth", tags=["auth"])
    get_db, principal = make_dependencies(settings)

    def payload(row):
        return {"accessToken": sign_token(row["user_id"], row["username"], settings.jwt_secret, settings.jwt_expires_in), "tokenType": "Bearer", "user": format_user(row)}

    @routes.post("/register", status_code=201)
    def register(input: RegistrationInput, connection: sqlite3.Connection = Depends(get_db)):
        return {"data": payload(create_user(connection, input))}

    @routes.post("/login")
    def login(input: LoginInput, connection: sqlite3.Connection = Depends(get_db)):
        account = find_credential(connection, input.identifier)
        matches = password_matches(input.password, account["password_hash"] if account else DUMMY_HASH)
        if not account or not matches or account["status"] != 1:
            raise ApiError(401, "INVALID_CREDENTIALS", "Invalid credentials.")
        return {"data": payload(public_user(connection, account["user_id"]))}

    @routes.get("/me")
    def me(user=Depends(principal), connection: sqlite3.Connection = Depends(get_db)):
        row = public_user(connection, user["user_id"])
        if not row or row["status"] != 1:
            raise ApiError(401, "INVALID_TOKEN", "Authentication token is invalid.")
        return {"data": {"user": format_user(row)}}

    return routes
