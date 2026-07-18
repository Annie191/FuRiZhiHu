from __future__ import annotations

import sqlite3

from ..db import transaction
from ..errors import ApiError
from ..schemas.auth import RegistrationInput
from ..security import hash_password

PUBLIC_PROJECTION = """
SELECT ua.user_id, ua.username, ua.nickname, ua.phone, ua.email, ua.status,
       up.age, up.gender, up.height_cm, up.weight_kg, up.goal, up.activity_level,
       up.avg_sleep_hours, up.water_target_ml, up.profile_tag, up.bmi
FROM user_account ua INNER JOIN user_profile up ON up.user_id = ua.user_id
"""


def format_user(row: sqlite3.Row) -> dict:
    return {
        "id": row["user_id"], "username": row["username"], "nickname": row["nickname"],
        "phone": row["phone"], "email": row["email"],
        "profile": {"age": row["age"], "gender": row["gender"], "heightCm": row["height_cm"],
                    "weightKg": row["weight_kg"], "goal": row["goal"], "activityLevel": row["activity_level"],
                    "avgSleepHours": row["avg_sleep_hours"], "waterTargetMl": row["water_target_ml"],
                    "profileTag": row["profile_tag"], "bmi": row["bmi"]},
    }


def find_credential(connection: sqlite3.Connection, identifier: str):
    return connection.execute("SELECT user_id, username, password_hash, status FROM user_account WHERE username = ? OR phone = ? OR email = ? LIMIT 1", (identifier, identifier, identifier)).fetchone()


def public_user(connection: sqlite3.Connection, user_id: int):
    return connection.execute(f"{PUBLIC_PROJECTION} WHERE ua.user_id = ?", (user_id,)).fetchone()


def create_user(connection: sqlite3.Connection, input: RegistrationInput):
    profile = input.profile
    try:
        with transaction(connection):
            result = connection.execute("INSERT INTO user_account (username, password_hash, nickname, phone, email) VALUES (?, ?, ?, ?, ?)", (input.username, hash_password(input.password), input.nickname, input.phone, input.email))
            user_id = result.lastrowid
            connection.execute("""INSERT INTO user_profile (user_id, age, gender, height_cm, weight_kg, goal, activity_level, avg_sleep_hours, water_target_ml, profile_tag)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (user_id, profile.age, profile.gender, profile.height_cm, profile.weight_kg, profile.goal, profile.activity_level, profile.avg_sleep_hours, profile.water_target_ml, profile.profile_tag))
            return public_user(connection, user_id)
    except sqlite3.IntegrityError as error:
        raise ApiError(409, "ACCOUNT_IDENTIFIER_TAKEN", "An account with those identifiers already exists.") from error
