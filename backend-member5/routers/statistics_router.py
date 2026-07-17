"""C 模块：数据统计 — C4 综合概览"""

import re

from fastapi import APIRouter, Query
from config import get_db, success, fail
from utils.health_score import get_grade

router = APIRouter()

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
