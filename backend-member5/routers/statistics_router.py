"""C 模块：数据统计 — C1 饮食 / C2 运动 / C3 睡眠 / C4 概览"""

import re

from fastapi import APIRouter, Query
from config import get_db, success, fail
from utils.health_score import get_grade

router = APIRouter()

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _check_dates(start_date: str, end_date: str):
    if not DATE_RE.match(start_date) or not DATE_RE.match(end_date):
        return fail("参数校验失败：日期格式应为 YYYY-MM-DD", code=1002)
    if start_date > end_date:
        return fail("参数校验失败：start_date 不能晚于 end_date", code=1002)
    return None


# ── C1：饮食统计 ────────────────────────────────────────────────────────


@router.get("/statistics/{user_id}/food")
def food_statistics(
    user_id: int,
    start_date: str = Query(..., description="起始 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束 YYYY-MM-DD"),
):
    err = _check_dates(start_date, end_date)
    if err:
        return err

    db = get_db()

    # 检查用户是否存在
    account = db.execute(
        "SELECT user_id FROM user_account WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not account:
        db.close()
        return fail("用户不存在", code=1001)

    daily = db.execute(
        """SELECT intake_date, total_calorie_kcal, total_protein_g, food_health_score
           FROM v_daily_food_summary
           WHERE user_id = ? AND intake_date BETWEEN ? AND ?
           ORDER BY intake_date""",
        (user_id, start_date, end_date),
    ).fetchall()

    meals = db.execute(
        """SELECT fr.meal_type,
                  ROUND(SUM(fl.calorie_kcal * fr.amount / 100.0), 2) AS total_cal,
                  COUNT(*) AS cnt
           FROM food_record fr
           JOIN food_library fl ON fl.food_id = fr.food_id
           WHERE fr.user_id = ? AND fr.intake_date BETWEEN ? AND ?
           GROUP BY fr.meal_type""",
        (user_id, start_date, end_date),
    ).fetchall()

    top_foods = db.execute(
        """SELECT fl.name, COUNT(*) AS cnt
           FROM food_record fr
           JOIN food_library fl ON fl.food_id = fr.food_id
           WHERE fr.user_id = ? AND fr.intake_date BETWEEN ? AND ?
           GROUP BY fl.name
           ORDER BY cnt DESC LIMIT 5""",
        (user_id, start_date, end_date),
    ).fetchall()

    db.close()

    if not daily:
        return success(
            {
                "period": {"start": start_date, "end": end_date},
                "daily_avg": {"calorie_kcal": 0, "protein_g": 0, "food_health_score": 0},
                "meal_distribution": {},
                "calories_trend": [],
                "top_foods": [],
                "summary": "暂无数据",
            }
        )

    avg_cal = round(sum(r["total_calorie_kcal"] for r in daily) / len(daily), 1)
    avg_protein = round(sum(r["total_protein_g"] for r in daily) / len(daily), 1)
    avg_food_score = round(sum(r["food_health_score"] for r in daily) / len(daily), 1)

    meal_dist = {}
    for m in meals:
        days = len(daily)
        meal_dist[m["meal_type"]] = {
            "avg_calories": round(m["total_cal"] / days, 1),
            "record_count": m["cnt"],
            "total_calories": round(m["total_cal"], 1),
        }

    calories_trend = [
        {"date": r["intake_date"], "calorie_kcal": r["total_calorie_kcal"]} for r in daily
    ]

    return success(
        {
            "period": {"start": start_date, "end": end_date},
            "daily_avg": {
                "calorie_kcal": avg_cal,
                "protein_g": avg_protein,
                "food_health_score": avg_food_score,
            },
            "meal_distribution": meal_dist,
            "calories_trend": calories_trend,
            "top_foods": [{"name": f["name"], "count": f["cnt"]} for f in top_foods],
            "summary": f"日均热量 {avg_cal} kcal；日均蛋白质 {avg_protein}g；饮食健康评分 {avg_food_score}",
        }
    )


# ── C2：运动统计 ────────────────────────────────────────────────────────


@router.get("/statistics/{user_id}/sport")
def sport_statistics(
    user_id: int,
    start_date: str = Query(..., description="起始 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束 YYYY-MM-DD"),
):
    err = _check_dates(start_date, end_date)
    if err:
        return err

    db = get_db()

    # 检查用户是否存在
    account = db.execute(
        "SELECT user_id FROM user_account WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not account:
        db.close()
        return fail("用户不存在", code=1001)

    daily = db.execute(
        """SELECT record_date, total_duration_min, total_calories_burned, sport_times
           FROM v_daily_sport_summary
           WHERE user_id = ? AND record_date BETWEEN ? AND ?
           ORDER BY record_date""",
        (user_id, start_date, end_date),
    ).fetchall()

    by_type = db.execute(
        """SELECT sport_type,
                  SUM(duration_min) AS total_min,
                  COUNT(*) AS cnt,
                  ROUND(SUM(calories_burned), 2) AS total_cal
           FROM sport_record
           WHERE user_id = ? AND record_date BETWEEN ? AND ?
           GROUP BY sport_type""",
        (user_id, start_date, end_date),
    ).fetchall()

    db.close()

    if not daily:
        return success(
            {
                "period": {"start": start_date, "end": end_date},
                "total_duration_min": 0,
                "total_calories_burned": 0,
                "active_days": 0,
                "sport_breakdown": {},
                "duration_trend": [],
                "completion_rate": 0,
                "summary": "暂无数据",
            }
        )

    total_min = int(sum(r["total_duration_min"] for r in daily))
    total_cal = round(sum(r["total_calories_burned"] for r in daily), 1)
    active_days = sum(1 for r in daily if r["total_duration_min"] > 0)

    from datetime import date as dt_date

    days_in_range = (dt_date.fromisoformat(end_date) - dt_date.fromisoformat(start_date)).days + 1
    completion_rate = round(active_days / days_in_range * 100, 1)

    breakdown = {
        bt["sport_type"]: {
            "total_min": bt["total_min"],
            "count": bt["cnt"],
            "total_calories": bt["total_cal"],
        }
        for bt in by_type
    }

    duration_trend = [
        {"date": r["record_date"], "duration_min": int(r["total_duration_min"])}
        for r in daily
    ]

    return success(
        {
            "period": {"start": start_date, "end": end_date},
            "total_duration_min": total_min,
            "total_calories_burned": total_cal,
            "active_days": active_days,
            "sport_breakdown": breakdown,
            "duration_trend": duration_trend,
            "completion_rate": completion_rate,
            "summary": f"共运动 {active_days} 天，总时长 {total_min} 分钟，消耗 {total_cal} kcal；完成率 {completion_rate}%",
        }
    )


# ── C3：睡眠统计 ────────────────────────────────────────────────────────


@router.get("/statistics/{user_id}/sleep")
def sleep_statistics(
    user_id: int,
    start_date: str = Query(..., description="起始 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束 YYYY-MM-DD"),
):
    err = _check_dates(start_date, end_date)
    if err:
        return err

    db = get_db()

    # 检查用户是否存在
    account = db.execute(
        "SELECT user_id FROM user_account WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not account:
        db.close()
        return fail("用户不存在", code=1001)

    daily = db.execute(
        """SELECT record_date, sleep_hours, sleep_quality_score
           FROM v_daily_sleep_summary
           WHERE user_id = ? AND record_date BETWEEN ? AND ?
           ORDER BY record_date""",
        (user_id, start_date, end_date),
    ).fetchall()

    extremes = db.execute(
        """SELECT MIN(time(sleep_time)) AS earliest,
                  MAX(time(sleep_time)) AS latest
           FROM sleep_record
           WHERE user_id = ? AND record_date BETWEEN ? AND ?""",
        (user_id, start_date, end_date),
    ).fetchone()

    db.close()

    if not daily:
        return success(
            {
                "period": {"start": start_date, "end": end_date},
                "avg_sleep_hours": 0,
                "avg_quality_score": 0,
                "earliest_sleep": None,
                "latest_sleep": None,
                "total_records": 0,
                "sleep_trend": [],
                "quality_distribution": {
                    "excellent": 0,
                    "good": 0,
                    "fair": 0,
                    "poor": 0,
                    "very_poor": 0,
                },
                "summary": "暂无数据",
            }
        )

    avg_hours = round(sum(r["sleep_hours"] for r in daily) / len(daily), 1)
    avg_quality = round(sum(r["sleep_quality_score"] for r in daily) / len(daily), 1)

    dist = {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "very_poor": 0}
    for r in daily:
        q = r["sleep_quality_score"]
        if q >= 90:
            dist["excellent"] += 1
        elif q >= 80:
            dist["good"] += 1
        elif q >= 60:
            dist["fair"] += 1
        elif q >= 40:
            dist["poor"] += 1
        else:
            dist["very_poor"] += 1

    return success(
        {
            "period": {"start": start_date, "end": end_date},
            "avg_sleep_hours": avg_hours,
            "avg_quality_score": avg_quality,
            "earliest_sleep": extremes["earliest"] if extremes else None,
            "latest_sleep": extremes["latest"] if extremes else None,
            "total_records": len(daily),
            "sleep_trend": [
                {
                    "date": r["record_date"],
                    "sleep_hours": r["sleep_hours"],
                    "quality_score": r["sleep_quality_score"],
                }
                for r in daily
            ],
            "quality_distribution": dist,
            "summary": f"平均睡眠 {avg_hours}h，质量评分 {avg_quality}；最早入睡 {extremes['earliest'] if extremes else '-'}，最晚 {extremes['latest'] if extremes else '-'}",
        }
    )


# ── C4：Dashboard 综合概览 ──────────────────────────────────────────────


@router.get("/statistics/{user_id}/overview")
def overview(user_id: int, date: str = Query(..., description="日期 YYYY-MM-DD")):
    if not DATE_RE.match(date):
        return fail("参数校验失败：日期格式应为 YYYY-MM-DD", code=1002)

    db = get_db()

    profile = db.execute(
        "SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not profile:
        db.close()
        return fail("用户画像不存在，请先创建画像", code=1001)

    row = db.execute(
        """SELECT d.health_score, d.water_ml, d.sport_duration_min,
                  d.food_health_score, d.sleep_hours, d.sleep_quality_score,
                  up.water_target_ml
           FROM v_dashboard_daily d
           JOIN user_profile up ON up.user_id = d.user_id
           WHERE d.user_id = ? AND d.stat_date = ?""",
        (user_id, date),
    ).fetchone()
    db.close()

    if not row:
        return success(
            {
                "date": date,
                "health_score": 0,
                "grade": "需改善",
                "task_completion": {
                    "water": {"current_ml": 0, "target_ml": 0, "percent": 0},
                    "sport": {"current_min": 0, "target_min": 30, "percent": 0},
                    "food": {"food_health_score": 0, "percent": 0},
                    "sleep": {"sleep_hours": 0, "quality_score": 0, "percent": 0},
                },
            }
        )

    water_target = row["water_target_ml"] or 2200

    return success(
        {
            "date": date,
            "health_score": round(row["health_score"], 1),
            "grade": get_grade(row["health_score"]),
            "task_completion": {
                "water": {
                    "current_ml": row["water_ml"],
                    "target_ml": water_target,
                    "percent": round(min(row["water_ml"] / water_target * 100, 100), 1)
                    if water_target > 0
                    else 0,
                },
                "sport": {
                    "current_min": row["sport_duration_min"],
                    "target_min": 30,
                    "percent": round(min(row["sport_duration_min"] / 30 * 100, 100), 1),
                },
                "food": {
                    "food_health_score": row["food_health_score"],
                    "percent": row["food_health_score"],
                },
                "sleep": {
                    "sleep_hours": row["sleep_hours"],
                    "quality_score": row["sleep_quality_score"],
                    "percent": row["sleep_quality_score"],
                },
            },
        }
    )
