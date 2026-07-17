"""B 模块：健康报告 — B1 每日 / B2 每周"""

import re
from datetime import date, timedelta

from fastapi import APIRouter, Query
from config import get_db, success, fail
from utils.health_score import get_grade

router = APIRouter()

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_date(d: str) -> bool:
    return bool(DATE_RE.match(d))


# ── B1：每日健康报告 ────────────────────────────────────────────────────


@router.get("/report/{user_id}/daily")
def daily_report(user_id: int, date: str = Query(..., description="日期 YYYY-MM-DD")):
    if not validate_date(date):
        return fail("参数校验失败：日期格式应为 YYYY-MM-DD", code=1002)

    db = get_db()

    profile = db.execute(
        "SELECT user_id, profile_tag, water_target_ml FROM user_profile WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    if not profile:
        db.close()
        return fail("用户画像不存在，请先创建画像", code=1001)

    dash = db.execute(
        """SELECT stat_date, health_score, water_ml, sport_duration_min,
                  food_health_score, sleep_hours, sleep_quality_score
           FROM v_dashboard_daily
           WHERE user_id = ? AND stat_date = ?""",
        (user_id, date),
    ).fetchone()

    db.close()

    water_actual = dash["water_ml"] if dash else 0
    water_target = profile["water_target_ml"]
    sport_actual = dash["sport_duration_min"] if dash else 0
    sport_target = 30

    data = {
        "date": date,
        "profile_tag": profile["profile_tag"],
        "health_score": round(dash["health_score"], 1) if dash else 0,
        "grade": get_grade(dash["health_score"] if dash else 0),
        "breakdown": {
            "water": {
                "actual": water_actual,
                "target": water_target,
                "completion": round(min(water_actual / water_target * 100, 100), 1) if water_target > 0 else 0,
                "weight": 0.30,
            },
            "sport": {
                "actual_min": sport_actual,
                "target_min": sport_target,
                "completion": round(min(sport_actual / sport_target * 100, 100), 1),
                "weight": 0.25,
            },
            "food": {
                "food_health_score": dash["food_health_score"] if dash else 0,
                "weight": 0.25,
            },
            "sleep": {
                "sleep_hours": dash["sleep_hours"] if dash else 0,
                "quality_score": dash["sleep_quality_score"] if dash else 0,
                "weight": 0.20,
            },
        },
    }
    return success(data)


# ── B2：每周健康报告 ────────────────────────────────────────────────────


@router.get("/report/{user_id}/weekly")
def weekly_report(
    user_id: int,
    start_date: str = Query(None, description="起始 YYYY-MM-DD，默认 7 天前"),
    end_date: str = Query(None, description="结束 YYYY-MM-DD，默认昨天"),
):
    # 默认日期
    today = date.today()
    if not end_date:
        end_date = (today - timedelta(days=1)).isoformat()
    if not start_date:
        start_date = (today - timedelta(days=7)).isoformat()

    if not validate_date(start_date) or not validate_date(end_date):
        return fail("参数校验失败：日期格式应为 YYYY-MM-DD", code=1002)
    if start_date > end_date:
        return fail("参数校验失败：start_date 不能晚于 end_date", code=1002)

    db = get_db()

    profile = db.execute(
        "SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not profile:
        db.close()
        return fail("用户画像不存在，请先创建画像", code=1001)

    rows = db.execute(
        """SELECT d.stat_date, d.health_score, d.water_ml, d.sport_duration_min,
                  d.food_health_score, d.sleep_hours, d.sleep_quality_score,
                  up.water_target_ml
           FROM v_dashboard_daily d
           JOIN user_profile up ON up.user_id = d.user_id
           WHERE d.user_id = ? AND d.stat_date BETWEEN ? AND ?
           ORDER BY d.stat_date""",
        (user_id, start_date, end_date),
    ).fetchall()
    db.close()

    if not rows:
        return success(
            {
                "period": {"start": start_date, "end": end_date},
                "avg_health_score": 0,
                "score_trend": [],
                "score_change": "0.0",
                "dimension_summary": {
                    "water": {"avg_ml": 0, "best_day": None, "worst_day": None},
                    "sport": {"total_min": 0, "active_days": 0, "best_day": None},
                    "food": {"avg_food_score": 0, "best_day": None},
                    "sleep": {"avg_hours": 0, "avg_quality": 0, "best_day": None},
                },
                "weekly_summary": "暂无数据",
            }
        )

    scores = [r["health_score"] for r in rows]
    water_vals = [(r["water_ml"], r["stat_date"]) for r in rows]
    sport_vals = [(r["sport_duration_min"], r["stat_date"]) for r in rows]
    food_vals = [(r["food_health_score"], r["stat_date"]) for r in rows]
    sleep_vals = [(r["sleep_quality_score"], r["stat_date"]) for r in rows]

    avg_score = round(sum(scores) / len(scores), 1)
    score_change_val = round(scores[-1] - scores[0], 1)
    score_change_str = f"{'+' if score_change_val >= 0 else ''}{score_change_val}"

    # 饮水
    avg_water = round(sum(w[0] for w in water_vals) / len(water_vals))
    best_water = max(water_vals, key=lambda x: x[0])
    worst_water = min(water_vals, key=lambda x: x[0])

    # 运动
    total_sport = int(sum(s[0] for s in sport_vals))
    active_days = sum(1 for s in sport_vals if s[0] > 0)
    best_sport = max(sport_vals, key=lambda x: x[0]) if total_sport > 0 else (0, None)

    # 饮食
    avg_food = round(sum(f[0] for f in food_vals) / len(food_vals), 1)
    best_food = max(food_vals, key=lambda x: x[0])

    # 睡眠
    avg_sleep_h = round(sum(r["sleep_hours"] for r in rows) / len(rows), 1)
    avg_sleep_q = round(sum(s[0] for s in sleep_vals) / len(sleep_vals), 1)
    best_sleep = max(sleep_vals, key=lambda x: x[0])

    weekly_summary = (
        f"本周运动 {active_days} 天，共 {total_sport} 分钟；"
        f"日均饮水 {avg_water}ml；"
        f"平均睡眠 {avg_sleep_h}h"
    )

    return success(
        {
            "period": {"start": start_date, "end": end_date},
            "avg_health_score": avg_score,
            "score_trend": scores,
            "score_change": score_change_str,
            "dimension_summary": {
                "water": {
                    "avg_ml": avg_water,
                    "best_day": best_water[1],
                    "worst_day": worst_water[1],
                },
                "sport": {
                    "total_min": total_sport,
                    "active_days": active_days,
                    "best_day": best_sport[1],
                },
                "food": {
                    "avg_food_score": avg_food,
                    "best_day": best_food[1],
                },
                "sleep": {
                    "avg_hours": avg_sleep_h,
                    "avg_quality": avg_sleep_q,
                    "best_day": best_sleep[1],
                },
            },
            "weekly_summary": weekly_summary,
        }
    )
