from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Query

from ..dependencies import make_dependencies
from ..errors import ApiError

CATEGORIES = {"fruit", "vegetable", "grain", "protein", "beverage", "other"}
SEASONS = {"spring", "summer", "autumn", "winter", "all"}


def map_food(row: sqlite3.Row) -> dict:
    return {"id": row["food_id"], "name": row["name"], "calorieKcal": row["calorie_kcal"], "proteinG": row["protein_g"], "waterMl": row["water_ml"], "category": row["category"], "season": row["season"], "unitBasis": row["unit_basis"], "note": row["note"]}


def router(settings) -> APIRouter:
    routes = APIRouter(prefix="/foods", tags=["foods"])
    get_db, _ = make_dependencies(settings)

    @routes.get("")
    def list_foods(q: str | None = Query(default=None, min_length=1, max_length=100), category: str | None = None, season: str | None = None, page: int = Query(default=1, ge=1), pageSize: int = Query(default=20, ge=1, le=100), connection: sqlite3.Connection = Depends(get_db)):
        if category and category not in CATEGORIES or season and season not in SEASONS:
            raise ApiError(400, "VALIDATION_ERROR", "Request validation failed.")
        clauses, values = [], []
        if q:
            clauses.append("name LIKE ?")
            values.append(f"%{q.strip()}%")
        if category:
            clauses.append("category = ?")
            values.append(category)
        if season:
            clauses.append("season = ?")
            values.append(season)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        total = connection.execute(f"SELECT COUNT(*) AS count FROM food_library {where}", values).fetchone()["count"]
        rows = connection.execute(f"SELECT * FROM food_library {where} ORDER BY name, food_id LIMIT ? OFFSET ?", [*values, pageSize, (page - 1) * pageSize]).fetchall()
        return {"data": {"items": [map_food(row) for row in rows], "page": page, "pageSize": pageSize, "total": total}}

    @routes.get("/{food_id}")
    def food_detail(food_id: int, connection: sqlite3.Connection = Depends(get_db)):
        if food_id <= 0:
            raise ApiError(400, "VALIDATION_ERROR", "Request validation failed.")
        row = connection.execute("SELECT * FROM food_library WHERE food_id = ?", (food_id,)).fetchone()
        if not row:
            raise ApiError(404, "RESOURCE_NOT_FOUND", "Food was not found.")
        return {"data": map_food(row)}

    return routes
