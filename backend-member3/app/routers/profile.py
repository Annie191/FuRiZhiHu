from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..dependencies import make_dependencies
from ..errors import ApiError
from ..schemas.common import require_nonempty
from ..schemas.profile import ProfilePatch

COLUMNS = {"age": "age", "gender": "gender", "height_cm": "height_cm", "weight_kg": "weight_kg", "goal": "goal", "activity_level": "activity_level", "avg_sleep_hours": "avg_sleep_hours", "water_target_ml": "water_target_ml", "profile_tag": "profile_tag"}
PROJECTION = "age, gender, height_cm, weight_kg, goal, activity_level, avg_sleep_hours, water_target_ml, profile_tag, bmi"


def map_profile(row: sqlite3.Row) -> dict:
    return {"age": row["age"], "gender": row["gender"], "heightCm": row["height_cm"], "weightKg": row["weight_kg"], "bmi": row["bmi"], "goal": row["goal"], "activityLevel": row["activity_level"], "avgSleepHours": row["avg_sleep_hours"], "waterTargetMl": row["water_target_ml"], "profileTag": row["profile_tag"]}


def get_profile(connection: sqlite3.Connection, user_id: int) -> dict:
    row = connection.execute(f"SELECT {PROJECTION} FROM user_profile WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Health profile was not found.")
    return map_profile(row)


def router(settings) -> APIRouter:
    routes = APIRouter(prefix="/profile", tags=["profile"])
    get_db, principal = make_dependencies(settings)

    @routes.get("")
    def profile(user=Depends(principal), connection: sqlite3.Connection = Depends(get_db)):
        return {"data": get_profile(connection, user["user_id"])}

    @routes.patch("")
    def update_profile(input: ProfilePatch, user=Depends(principal), connection: sqlite3.Connection = Depends(get_db)):
        require_nonempty(input)
        changes = input.model_dump(exclude_unset=True)
        assignments = ", ".join(f"{COLUMNS[key]} = ?" for key in changes)
        connection.execute(f"UPDATE user_profile SET {assignments} WHERE user_id = ?", (*changes.values(), user["user_id"]))
        return {"data": get_profile(connection, user["user_id"])}

    return routes
