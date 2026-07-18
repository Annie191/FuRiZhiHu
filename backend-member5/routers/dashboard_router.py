"""前端 Dashboard 聚合接口。"""

import re
from datetime import date

from fastapi import APIRouter, Query

from config import fail, get_db, success
from utils.health_score import get_grade

router = APIRouter()

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

GENDER_LABELS = {
    "male": "男",
    "female": "女",
    "other": "其他",
}

GOAL_LABELS = {
    "lose_fat": "减脂",
    "maintain": "保持健康",
    "gain_muscle": "增肌",
}

ACTIVITY_LABELS = {
    "low": "较少运动",
    "medium": "规律运动",
    "high": "高频运动",
}

RISK_LABELS = {
    "low": "低风险",
    "medium": "中等风险",
    "high": "高风险",
    "extreme": "极高风险",
}


def _build_overview(row, water_target: int, target_date: str) -> dict:
    if not row:
        return {
            "date": target_date,
            "health_score": 0,
            "grade": "需改善",
            "task_completion": {
                "water": {"current_ml": 0, "target_ml": water_target, "percent": 0},
                "sport": {"current_min": 0, "target_min": 30, "percent": 0},
                "food": {"food_health_score": 0, "percent": 0},
                "sleep": {"sleep_hours": 0, "quality_score": 0, "percent": 0},
            },
        }

    water_ml = row["water_ml"] or 0
    sport_min = row["sport_duration_min"] or 0
    food_score = row["food_health_score"] or 0
    sleep_score = row["sleep_quality_score"] or 0

    return {
        "date": target_date,
        "health_score": round(row["health_score"] or 0, 1),
        "grade": get_grade(row["health_score"] or 0),
        "task_completion": {
            "water": {
                "current_ml": water_ml,
                "target_ml": water_target,
                "percent": round(min(water_ml / water_target * 100, 100), 1) if water_target > 0 else 0,
            },
            "sport": {
                "current_min": sport_min,
                "target_min": 30,
                "percent": round(min(sport_min / 30 * 100, 100), 1),
            },
            "food": {
                "food_health_score": round(food_score, 1),
                "percent": round(food_score, 1),
            },
            "sleep": {
                "sleep_hours": round(row["sleep_hours"] or 0, 1),
                "quality_score": round(sleep_score, 1),
                "percent": round(sleep_score, 1),
            },
        },
    }


@router.get("/dashboard/users")
def users():
    db = get_db()
    try:
        rows = db.execute(
            """SELECT ua.user_id, ua.username, ua.nickname, up.profile_tag,
                      MAX(d.stat_date) AS latest_date
               FROM user_account ua
               INNER JOIN user_profile up ON up.user_id = ua.user_id
               LEFT JOIN v_dashboard_daily d ON d.user_id = ua.user_id
               WHERE ua.status = 1
               GROUP BY ua.user_id, ua.username, ua.nickname, up.profile_tag
               ORDER BY ua.user_id"""
        ).fetchall()
        return success(
            [
                {
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "nickname": row["nickname"],
                    "profile_tag": row["profile_tag"],
                    "latest_date": row["latest_date"],
                }
                for row in rows
            ]
        )
    finally:
        db.close()


@router.get("/dashboard/{user_id}")
def dashboard(
    user_id: int,
    target_date: str | None = Query(None, alias="date", description="日期 YYYY-MM-DD，默认使用该用户最新数据日期"),
    city: str = Query("上海", description="天气城市"),
):
    if target_date and not DATE_RE.match(target_date):
        return fail("参数校验失败：日期格式应为 YYYY-MM-DD", code=1002)

    db = get_db()
    try:
        profile = db.execute(
            """SELECT ua.user_id, ua.username, ua.nickname,
                      up.age, up.gender, up.height_cm, up.weight_kg, up.bmi,
                      up.goal, up.activity_level, up.avg_sleep_hours,
                      up.water_target_ml, up.profile_tag
               FROM user_account ua
               INNER JOIN user_profile up ON up.user_id = ua.user_id
               WHERE ua.user_id = ? AND ua.status = 1""",
            (user_id,),
        ).fetchone()
        if not profile:
            return fail("用户画像不存在，请先创建画像", code=1001)

        available_dates = [
            row["stat_date"]
            for row in db.execute(
                """SELECT DISTINCT stat_date
                   FROM v_dashboard_daily
                   WHERE user_id = ?
                   ORDER BY stat_date DESC""",
                (user_id,),
            ).fetchall()
        ]
        selected_date = target_date or (available_dates[0] if available_dates else date.today().isoformat())

        cities = [
            row["city"]
            for row in db.execute(
                "SELECT DISTINCT city FROM weather_daily ORDER BY city"
            ).fetchall()
        ]

        dashboard_row = db.execute(
            """SELECT health_score, water_ml, sport_duration_min,
                      food_health_score, sleep_hours, sleep_quality_score
               FROM v_dashboard_daily
               WHERE user_id = ? AND stat_date = ?""",
            (user_id, selected_date),
        ).fetchone()

        weather = db.execute(
            """SELECT city, weather_date, temperature_c, humidity_pct, uv_index,
                      air_quality_index, heat_risk, advice
               FROM weather_daily
               WHERE city = ? AND weather_date = ?""",
            (city, selected_date),
        ).fetchone()

        plan = db.execute(
            """SELECT breakfast_advice, midday_advice, exercise_advice,
                      evening_advice, health_target_score, status
               FROM daily_plan
               WHERE user_id = ? AND plan_date = ?""",
            (user_id, selected_date),
        ).fetchone()

        water_target = profile["water_target_ml"] or 2200
        return success(
            {
                "selected_date": selected_date,
                "available_dates": available_dates,
                "selected_city": city,
                "available_cities": cities,
                "user": {
                    "user_id": profile["user_id"],
                    "username": profile["username"],
                    "nickname": profile["nickname"],
                },
                "profile": {
                    "age": profile["age"],
                    "gender": profile["gender"],
                    "gender_label": GENDER_LABELS.get(profile["gender"], profile["gender"]),
                    "height_cm": profile["height_cm"],
                    "weight_kg": profile["weight_kg"],
                    "bmi": profile["bmi"],
                    "goal": profile["goal"],
                    "goal_label": GOAL_LABELS.get(profile["goal"], profile["goal"]),
                    "activity_level": profile["activity_level"],
                    "activity_label": ACTIVITY_LABELS.get(profile["activity_level"], profile["activity_level"]),
                    "avg_sleep_hours": profile["avg_sleep_hours"],
                    "water_target_ml": water_target,
                    "profile_tag": profile["profile_tag"],
                },
                "overview": _build_overview(dashboard_row, water_target, selected_date),
                "weather": {
                    "city": weather["city"],
                    "date": weather["weather_date"],
                    "temperature_c": weather["temperature_c"],
                    "humidity_pct": weather["humidity_pct"],
                    "uv_index": weather["uv_index"],
                    "air_quality_index": weather["air_quality_index"],
                    "heat_risk": weather["heat_risk"],
                    "heat_risk_label": RISK_LABELS.get(weather["heat_risk"], weather["heat_risk"]),
                    "advice": weather["advice"],
                }
                if weather
                else None,
                "plan": {
                    "breakfast_advice": plan["breakfast_advice"],
                    "midday_advice": plan["midday_advice"],
                    "exercise_advice": plan["exercise_advice"],
                    "evening_advice": plan["evening_advice"],
                    "health_target_score": plan["health_target_score"],
                    "status": plan["status"],
                }
                if plan
                else None,
            }
        )
    finally:
        db.close()
