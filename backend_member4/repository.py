"""成员 4 天气和计划结果的 SQLite 持久化。"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any, Mapping


class PersistenceError(RuntimeError):
    """推荐结果无法可靠写入数据库。"""


class RecommendationRepository:
    """使用 UPSERT 保存天气与每日计划，并保留原有主键。"""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def upsert_plan(
        self,
        user_id: int,
        plan_date: str,
        result: Mapping[str, Any],
        health_target_score: int = 80,
        status: str = "pending",
    ) -> int:
        if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id 必须是正整数。")
        self._validate_date(plan_date)
        if isinstance(health_target_score, bool) or not isinstance(health_target_score, int) or not 0 <= health_target_score <= 100:
            raise ValueError("health_target_score 必须是 0 到 100 的整数。")
        if status not in {"pending", "completed"}:
            raise ValueError("status 只能是 pending 或 completed。")
        plan = result.get("plan") if isinstance(result, Mapping) else None
        required = ("breakfast_advice", "midday_advice", "exercise_advice", "evening_advice")
        if not isinstance(plan, Mapping) or any(not isinstance(plan.get(key), str) or not plan[key].strip() for key in required):
            raise ValueError("result.plan 缺少有效的四时段建议。")
        sql = """
            INSERT INTO daily_plan (
                user_id, plan_date, breakfast_advice, midday_advice,
                exercise_advice, evening_advice, health_target_score, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, plan_date) DO UPDATE SET
                breakfast_advice = excluded.breakfast_advice,
                midday_advice = excluded.midday_advice,
                exercise_advice = excluded.exercise_advice,
                evening_advice = excluded.evening_advice,
                health_target_score = excluded.health_target_score,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
        """
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect()
            with connection:
                connection.execute(sql, (
                    user_id,
                    plan_date,
                    plan["breakfast_advice"],
                    plan["midday_advice"],
                    plan["exercise_advice"],
                    plan["evening_advice"],
                    health_target_score,
                    status,
                ))
                row = connection.execute(
                    "SELECT plan_id FROM daily_plan WHERE user_id = ? AND plan_date = ?",
                    (user_id, plan_date),
                ).fetchone()
                if row is None:
                    raise sqlite3.DatabaseError("写入后未找到 daily_plan。")
                return int(row[0])
        except sqlite3.Error as error:
            raise PersistenceError("保存每日计划失败。") from error
        finally:
            if connection is not None:
                connection.close()

    def upsert_weather(self, assessment: Mapping[str, Any]) -> int:
        normalized = assessment.get("normalized_weather") if isinstance(assessment, Mapping) else None
        if not isinstance(normalized, Mapping) or not isinstance(normalized.get("city"), str) or not normalized["city"].strip():
            raise ValueError("天气评估必须包含 city。")
        weather_date = normalized.get("weather_date")
        self._validate_date(weather_date)
        advice = assessment.get("advice")
        if not isinstance(advice, list) or not advice or not all(isinstance(item, str) and item.strip() for item in advice):
            raise ValueError("天气评估必须包含建议列表。")
        sql = """
            INSERT INTO weather_daily (
                city, weather_date, temperature_c, humidity_pct, uv_index,
                air_quality_index, heat_risk, advice
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city, weather_date) DO UPDATE SET
                temperature_c = excluded.temperature_c,
                humidity_pct = excluded.humidity_pct,
                uv_index = excluded.uv_index,
                air_quality_index = excluded.air_quality_index,
                heat_risk = excluded.heat_risk,
                advice = excluded.advice
        """
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect()
            with connection:
                connection.execute(sql, (
                    normalized["city"],
                    weather_date,
                    normalized["temperature_c"],
                    int(round(normalized["humidity_pct"])),
                    int(round(normalized["uv_index"])),
                    int(round(normalized["air_quality_index"])),
                    assessment["risk_level"],
                    "\n".join(advice),
                ))
                row = connection.execute(
                    "SELECT weather_id FROM weather_daily WHERE city = ? AND weather_date = ?",
                    (normalized["city"], weather_date),
                ).fetchone()
                if row is None:
                    raise sqlite3.DatabaseError("写入后未找到 weather_daily。")
                return int(row[0])
        except sqlite3.Error as error:
            raise PersistenceError("保存天气评估失败。") from error
        finally:
            if connection is not None:
                connection.close()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    @staticmethod
    def _validate_date(value: Any) -> None:
        if not isinstance(value, str):
            raise ValueError("日期必须是 YYYY-MM-DD 字符串。")
        try:
            parsed = date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("日期必须是有效的 YYYY-MM-DD。") from error
        if parsed.isoformat() != value:
            raise ValueError("日期必须是 YYYY-MM-DD 格式。")
