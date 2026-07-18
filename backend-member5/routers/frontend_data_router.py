"""前端图表和列表使用的只读数据接口。"""

import re
from datetime import date, timedelta

from fastapi import APIRouter, Query

from config import fail, get_db, success

router = APIRouter()

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RISK_LABELS = {
    "low": "低风险",
    "medium": "中等风险",
    "high": "高风险",
    "extreme": "极高风险",
}


def _default_range(from_date: str | None, to_date: str | None) -> tuple[str, str] | None:
    if from_date and not DATE_RE.match(from_date):
        return None
    if to_date and not DATE_RE.match(to_date):
        return None
    end = to_date or date.today().isoformat()
    start = from_date or (date.fromisoformat(end) - timedelta(days=6)).isoformat()
    if start > end:
        return None
    return start, end


@router.get("/dashboard/{user_id}/series")
def dashboard_series(
    user_id: int,
    from_date: str | None = Query(None, alias="from", description="起始日期 YYYY-MM-DD"),
    to_date: str | None = Query(None, alias="to", description="结束日期 YYYY-MM-DD"),
):
    date_range = _default_range(from_date, to_date)
    if not date_range:
        return fail("参数校验失败：日期范围不合法", code=1002)
    start, end = date_range

    db = get_db()
    try:
        profile = db.execute("SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,)).fetchone()
        if not profile:
            return fail("用户画像不存在，请先创建画像", code=1001)
        rows = db.execute(
            """SELECT stat_date, health_score, water_ml, sport_duration_min,
                      sport_calories_burned, food_calorie_kcal, food_protein_g,
                      food_health_score, sleep_hours, sleep_quality_score
               FROM v_dashboard_daily
               WHERE user_id = ? AND stat_date BETWEEN ? AND ?
               ORDER BY stat_date""",
            (user_id, start, end),
        ).fetchall()
        return success(
            {
                "period": {"start": start, "end": end},
                "items": [
                    {
                        "date": row["stat_date"],
                        "healthScore": round(row["health_score"] or 0, 1),
                        "waterMl": row["water_ml"] or 0,
                        "sportDurationMin": row["sport_duration_min"] or 0,
                        "sportCaloriesBurned": row["sport_calories_burned"] or 0,
                        "foodCalorieKcal": row["food_calorie_kcal"] or 0,
                        "foodProteinG": row["food_protein_g"] or 0,
                        "foodHealthScore": round(row["food_health_score"] or 0, 1),
                        "sleepHours": round(row["sleep_hours"] or 0, 1),
                        "sleepQualityScore": round(row["sleep_quality_score"] or 0, 1),
                    }
                    for row in rows
                ],
            }
        )
    finally:
        db.close()


@router.get("/plans/{user_id}")
def plans(
    user_id: int,
    from_date: str | None = Query(None, alias="from", description="起始日期 YYYY-MM-DD"),
    to_date: str | None = Query(None, alias="to", description="结束日期 YYYY-MM-DD"),
):
    date_range = _default_range(from_date, to_date)
    if not date_range:
        return fail("参数校验失败：日期范围不合法", code=1002)
    start, end = date_range

    db = get_db()
    try:
        profile = db.execute("SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,)).fetchone()
        if not profile:
            return fail("用户画像不存在，请先创建画像", code=1001)
        rows = db.execute(
            """SELECT plan_id, plan_date, breakfast_advice, midday_advice,
                      exercise_advice, evening_advice, health_target_score, status
               FROM daily_plan
               WHERE user_id = ? AND plan_date BETWEEN ? AND ?
               ORDER BY plan_date DESC""",
            (user_id, start, end),
        ).fetchall()
        return success(
            {
                "period": {"start": start, "end": end},
                "items": [
                    {
                        "id": row["plan_id"],
                        "date": row["plan_date"],
                        "breakfastAdvice": row["breakfast_advice"],
                        "middayAdvice": row["midday_advice"],
                        "exerciseAdvice": row["exercise_advice"],
                        "eveningAdvice": row["evening_advice"],
                        "healthTargetScore": row["health_target_score"],
                        "status": row["status"],
                    }
                    for row in rows
                ],
            }
        )
    finally:
        db.close()


@router.get("/weather")
def weather(
    city: str = Query("上海", description="城市"),
    from_date: str | None = Query(None, alias="from", description="起始日期 YYYY-MM-DD"),
    to_date: str | None = Query(None, alias="to", description="结束日期 YYYY-MM-DD"),
):
    date_range = _default_range(from_date, to_date)
    if not date_range:
        return fail("参数校验失败：日期范围不合法", code=1002)
    start, end = date_range

    db = get_db()
    try:
        rows = db.execute(
            """SELECT weather_id, city, weather_date, temperature_c, humidity_pct,
                      uv_index, air_quality_index, heat_risk, advice
               FROM weather_daily
               WHERE city = ? AND weather_date BETWEEN ? AND ?
               ORDER BY weather_date""",
            (city, start, end),
        ).fetchall()
        return success(
            {
                "period": {"start": start, "end": end},
                "city": city,
                "items": [
                    {
                        "id": row["weather_id"],
                        "city": row["city"],
                        "date": row["weather_date"],
                        "temperatureC": row["temperature_c"],
                        "humidityPct": row["humidity_pct"],
                        "uvIndex": row["uv_index"],
                        "airQualityIndex": row["air_quality_index"],
                        "heatRisk": row["heat_risk"],
                        "heatRiskLabel": RISK_LABELS.get(row["heat_risk"], row["heat_risk"]),
                        "advice": row["advice"],
                    }
                    for row in rows
                ],
            }
        )
    finally:
        db.close()


@router.get("/community/posts")
def community_posts(limit: int = Query(20, ge=1, le=100)):
    db = get_db()
    try:
        rows = db.execute(
            """SELECT cp.post_id, cp.content, cp.posted_at, cp.likes_count,
                      ua.nickname, ua.username
               FROM community_post cp
               INNER JOIN user_account ua ON ua.user_id = cp.user_id
               WHERE cp.visibility = 'public' AND cp.status = 1
               ORDER BY cp.posted_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return success(
            [
                {
                    "id": row["post_id"],
                    "author": row["nickname"] or row["username"],
                    "content": row["content"],
                    "postedAt": row["posted_at"],
                    "likesCount": row["likes_count"],
                }
                for row in rows
            ]
        )
    finally:
        db.close()
