import sqlite3
from dataclasses import dataclass
from typing import Any, Type

from fastapi import APIRouter, Depends
from pydantic import BaseModel, create_model

from ..dependencies import make_dependencies
from ..errors import ApiError
from ..schemas.common import ListQuery, require_nonempty
from ..schemas.records import FoodRecordInput, SleepRecordInput, SportRecordInput, WaterRecordInput


@dataclass(frozen=True)
class RecordSpec:
    table: str
    view: str
    date_column: str
    summary_date: str
    input_model: Type[BaseModel]
    columns: dict[str, str]


SPECS = {
    "food": RecordSpec("food_record", "v_daily_food_summary", "intake_date", "intake_date", FoodRecordInput, {"food_id": "food_id", "meal_type": "meal_type", "amount": "amount", "amount_unit": "amount_unit", "intake_date": "intake_date", "note": "note"}),
    "water": RecordSpec("water_record", "v_daily_water_summary", "date(intake_time)", "stat_date", WaterRecordInput, {"amount_ml": "amount_ml", "source": "source", "intake_time": "intake_time", "note": "note"}),
    "sport": RecordSpec("sport_record", "v_daily_sport_summary", "record_date", "record_date", SportRecordInput, {"sport_type": "sport_type", "intensity": "intensity", "duration_min": "duration_min", "calories_burned": "calories_burned", "record_date": "record_date", "start_time": "start_time", "note": "note"}),
    "sleep": RecordSpec("sleep_record", "v_daily_sleep_summary", "record_date", "record_date", SleepRecordInput, {"sleep_time": "sleep_time", "wake_time": "wake_time", "quality_score": "quality_score", "record_date": "record_date", "note": "note"}),
}


def patch_model(model: Type[BaseModel]) -> Type[BaseModel]:
    fields = {name: (field.annotation | None, None) for name, field in model.model_fields.items()}
    return create_model(f"{model.__name__}Patch", __base__=model, **fields)


def map_record(kind: str, row: sqlite3.Row) -> dict[str, Any]:
    base = {"id": row["record_id"], "note": row["note"]}
    if kind == "food":
        return {**base, "foodId": row["food_id"], "mealType": row["meal_type"], "amount": row["amount"], "amountUnit": row["amount_unit"], "intakeDate": row["intake_date"], "food": {"id": row["food_id"], "name": row["food_name"], "calorieKcal": row["calorie_kcal"], "proteinG": row["protein_g"], "waterMl": row["water_ml"], "unitBasis": row["unit_basis"]}}
    if kind == "water":
        return {**base, "amountMl": row["amount_ml"], "source": row["source"], "intakeTime": row["intake_time"]}
    if kind == "sport":
        return {**base, "sportType": row["sport_type"], "intensity": row["intensity"], "durationMin": row["duration_min"], "caloriesBurned": row["calories_burned"], "recordDate": row["record_date"], "startTime": row["start_time"]}
    return {**base, "sleepTime": row["sleep_time"], "wakeTime": row["wake_time"], "qualityScore": row["quality_score"], "recordDate": row["record_date"]}


def map_summary(kind: str, row: sqlite3.Row) -> dict[str, Any]:
    if kind == "food":
        return {"date": row["intake_date"], "totalCalorieKcal": row["total_calorie_kcal"], "totalProteinG": row["total_protein_g"], "totalFoodWaterMl": row["total_food_water_ml"], "foodHealthScore": row["food_health_score"]}
    if kind == "water":
        return {"date": row["stat_date"], "totalWaterMl": row["total_water_ml"], "drinkTimes": row["drink_times"]}
    if kind == "sport":
        return {"date": row["record_date"], "totalDurationMin": row["total_duration_min"], "totalCaloriesBurned": row["total_calories_burned"], "sportTimes": row["sport_times"]}
    return {"date": row["record_date"], "sleepHours": row["sleep_hours"], "sleepQualityScore": row["sleep_quality_score"]}


def row_query(kind: str) -> str:
    spec = SPECS[kind]
    extra = ", f.name AS food_name, f.calorie_kcal, f.protein_g, f.water_ml, f.unit_basis" if kind == "food" else ""
    join = " JOIN food_library f ON f.food_id = r.food_id" if kind == "food" else ""
    return f"SELECT r.*{extra} FROM {spec.table} r{join}"


def find_owned(connection: sqlite3.Connection, kind: str, record_id: int, user_id: int) -> dict:
    row = connection.execute(f"{row_query(kind)} WHERE r.record_id = ? AND r.user_id = ?", (record_id, user_id)).fetchone()
    if not row:
        raise ApiError(404, "RESOURCE_NOT_FOUND", "Record was not found.")
    return map_record(kind, row)


def validate_domain(connection: sqlite3.Connection, kind: str, values: dict[str, Any]) -> None:
    if kind == "sleep":
        if values["wake_time"] <= values["sleep_time"]:
            raise ApiError(400, "VALIDATION_ERROR", "wakeTime must be later than sleepTime.")
        if values["record_date"] != values["wake_time"][:10]:
            raise ApiError(400, "VALIDATION_ERROR", "recordDate must match wakeTime date.")
    if kind == "food":
        food = connection.execute("SELECT unit_basis FROM food_library WHERE food_id = ?", (values["food_id"],)).fetchone()
        if not food:
            raise ApiError(400, "VALIDATION_ERROR", "Food does not exist.")
        expected = "g" if food["unit_basis"] == "per_100g" else "ml"
        if values["amount_unit"] != expected:
            raise ApiError(400, "VALIDATION_ERROR", f"Food amountUnit must be {expected}.")


def router(settings) -> APIRouter:
    routes = APIRouter(tags=["records"])
    get_db, principal = make_dependencies(settings)

    for kind, spec in SPECS.items():
        path = f"/{kind}-records"
        create = spec.input_model
        patch = patch_model(create)

        def summaries(query: ListQuery = Depends(), user=Depends(principal), connection: sqlite3.Connection = Depends(get_db), _kind=kind, _spec=spec):
            query.validate_range()
            clauses, values = ["user_id = ?"], [user["user_id"]]
            if query.date:
                clauses.append(f"{_spec.summary_date} = ?")
                values.append(query.date)
            elif query.from_date:
                clauses.append(f"{_spec.summary_date} BETWEEN ? AND ?")
                values.extend([query.from_date, query.to])
            rows = connection.execute(f"SELECT * FROM {_spec.view} WHERE {' AND '.join(clauses)} ORDER BY {_spec.summary_date}", values).fetchall()
            return {"data": [map_summary(_kind, row) for row in rows]}

        def list_records(query: ListQuery = Depends(), user=Depends(principal), connection: sqlite3.Connection = Depends(get_db), _kind=kind, _spec=spec):
            query.validate_range()
            clauses, values = ["r.user_id = ?"], [user["user_id"]]
            field = _spec.date_column if _kind != "water" else "date(r.intake_time)"
            if query.date:
                clauses.append(f"{field} = ?")
                values.append(query.date)
            elif query.from_date:
                clauses.append(f"{field} BETWEEN ? AND ?")
                values.extend([query.from_date, query.to])
            where = " AND ".join(clauses)
            join = " JOIN food_library f ON f.food_id = r.food_id" if _kind == "food" else ""
            total = connection.execute(f"SELECT COUNT(*) AS count FROM {_spec.table} r{join} WHERE {where}", values).fetchone()["count"]
            order = "r.intake_time" if _kind == "water" else f"r.{_spec.date_column}"
            rows = connection.execute(f"{row_query(_kind)} WHERE {where} ORDER BY {order} DESC, r.record_id DESC LIMIT ? OFFSET ?", [*values, query.page_size, (query.page - 1) * query.page_size]).fetchall()
            return {"data": {"items": [map_record(_kind, row) for row in rows], "page": query.page, "pageSize": query.page_size, "total": total}}

        def create_record(input: create, user=Depends(principal), connection: sqlite3.Connection = Depends(get_db), _kind=kind, _spec=spec):
            values = input.model_dump()
            validate_domain(connection, _kind, values)
            keys = list(values)
            result = connection.execute(f"INSERT INTO {_spec.table} (user_id, {', '.join(_spec.columns[key] for key in keys)}) VALUES (?, {', '.join('?' for _ in keys)})", (user["user_id"], *(values[key] for key in keys)))
            return {"data": find_owned(connection, _kind, result.lastrowid, user["user_id"])}

        def detail(record_id: int, user=Depends(principal), connection: sqlite3.Connection = Depends(get_db), _kind=kind):
            if record_id <= 0:
                raise ApiError(400, "VALIDATION_ERROR", "Request validation failed.")
            return {"data": find_owned(connection, _kind, record_id, user["user_id"])}

        def update_record(record_id: int, input: patch, user=Depends(principal), connection: sqlite3.Connection = Depends(get_db), _kind=kind, _spec=spec):
            if record_id <= 0:
                raise ApiError(400, "VALIDATION_ERROR", "Request validation failed.")
            require_nonempty(input)
            current = find_owned(connection, _kind, record_id, user["user_id"])
            current_values = {key: current.get(alias) for key, alias in {"food_id": "foodId", "meal_type": "mealType", "amount": "amount", "amount_unit": "amountUnit", "intake_date": "intakeDate", "amount_ml": "amountMl", "source": "source", "intake_time": "intakeTime", "sport_type": "sportType", "intensity": "intensity", "duration_min": "durationMin", "calories_burned": "caloriesBurned", "record_date": "recordDate", "start_time": "startTime", "sleep_time": "sleepTime", "wake_time": "wakeTime", "quality_score": "qualityScore", "note": "note"}.items() if key in _spec.columns}
            changes = input.model_dump(exclude_unset=True)
            validate_domain(connection, _kind, {**current_values, **changes})
            assignments = ", ".join(f"{_spec.columns[key]} = ?" for key in changes)
            connection.execute(f"UPDATE {_spec.table} SET {assignments} WHERE record_id = ? AND user_id = ?", (*changes.values(), record_id, user["user_id"]))
            return {"data": find_owned(connection, _kind, record_id, user["user_id"])}

        def delete_record(record_id: int, user=Depends(principal), connection: sqlite3.Connection = Depends(get_db), _spec=spec):
            if record_id <= 0:
                raise ApiError(400, "VALIDATION_ERROR", "Request validation failed.")
            result = connection.execute(f"DELETE FROM {_spec.table} WHERE record_id = ? AND user_id = ?", (record_id, user["user_id"]))
            if not result.rowcount:
                raise ApiError(404, "RESOURCE_NOT_FOUND", "Record was not found.")
            return None

        routes.add_api_route(f"{path}/daily-summary", summaries, methods=["GET"])
        routes.add_api_route(path, list_records, methods=["GET"])
        routes.add_api_route(path, create_record, methods=["POST"], status_code=201)
        routes.add_api_route(f"{path}/{{record_id}}", detail, methods=["GET"])
        routes.add_api_route(f"{path}/{{record_id}}", update_record, methods=["PATCH"])
        routes.add_api_route(f"{path}/{{record_id}}", delete_record, methods=["DELETE"], status_code=204)

    return routes
