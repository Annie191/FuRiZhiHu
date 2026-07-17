"""D 模块：趋势分析 — D1 健康指数趋势 / D2 综合趋势总结"""

from datetime import date, timedelta

import numpy as np
from fastapi import APIRouter, Query

from config import get_db, success, fail
from services.trend_analyzer import calc_trend, generate_assessment

router = APIRouter()


# ── D1：健康指数趋势 ────────────────────────────────────────────────────


@router.get("/trend/{user_id}/health-score")
def health_score_trend(
    user_id: int,
    days: int = Query(30, ge=7, le=90, description="统计天数，默认 30"),
):
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    db = get_db()

    profile = db.execute(
        "SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not profile:
        db.close()
        return fail("用户画像不存在，请先创建画像", code=1001)

    rows = db.execute(
        """SELECT stat_date, health_score
           FROM v_dashboard_daily
           WHERE user_id = ? AND stat_date BETWEEN ? AND ?
           ORDER BY stat_date""",
        (user_id, start_date.isoformat(), end_date.isoformat()),
    ).fetchall()
    db.close()

    if not rows:
        return success(
            {
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "days": days,
                "current": 0,
                "avg": 0,
                "max": 0,
                "min": 0,
                "change": "0.0",
                "trend": "数据不足",
                "slope": None,
                "chart_data": [],
            }
        )

    scores = [r["health_score"] for r in rows]

    current = round(scores[-1], 1)
    avg = round(np.mean(scores), 1)
    max_val = round(np.max(scores), 1)
    min_val = round(np.min(scores), 1)
    change_val = round(scores[-1] - scores[0], 1)
    change_str = f"{'+' if change_val >= 0 else ''}{change_val}"

    if len(scores) < 7:
        trend = "数据不足"
        slope = None
    else:
        trend = calc_trend(scores)
        x = np.arange(len(scores))
        y = np.array(scores, dtype=float)
        slope_val, _ = np.polyfit(x, y, 1)
        slope = round(float(slope_val), 4)

    chart_data = [
        {"date": r["stat_date"], "score": round(r["health_score"], 1)} for r in rows
    ]

    return success(
        {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "days": days,
            "current": current,
            "avg": avg,
            "max": max_val,
            "min": min_val,
            "change": change_str,
            "trend": trend,
            "slope": slope,
            "chart_data": chart_data,
        }
    )


# ── D2：综合趋势总结 ────────────────────────────────────────────────────


@router.get("/trend/{user_id}/summary")
def trend_summary(
    user_id: int,
    days: int = Query(30, ge=7, le=90, description="统计天数，默认 30"),
):
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    db = get_db()

    profile = db.execute(
        "SELECT user_id, goal FROM user_profile WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not profile:
        db.close()
        return fail("用户画像不存在，请先创建画像", code=1001)

    rows = db.execute(
        """SELECT stat_date, health_score, water_ml, sport_duration_min,
                  food_health_score, sleep_hours, sleep_quality_score
           FROM v_dashboard_daily
           WHERE user_id = ? AND stat_date BETWEEN ? AND ?
           ORDER BY stat_date""",
        (user_id, start_date.isoformat(), end_date.isoformat()),
    ).fetchall()
    db.close()

    if len(rows) < 7:
        return success(
            {
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "days": days,
                "health_score": {"current": 0, "avg": 0, "trend": "数据不足"},
                "water": {"avg_ml": 0, "trend": "数据不足"},
                "sport": {"total_min": 0, "trend": "数据不足"},
                "sleep": {"avg_hours": 0, "avg_quality": 0, "trend": "数据不足"},
                "food": {"avg_food_score": 0, "trend": "数据不足"},
                "overall_assessment": "有效数据不足7天，无法生成趋势分析。请持续记录健康数据。",
            }
        )

    health_scores = [r["health_score"] for r in rows]
    water_vals = [r["water_ml"] for r in rows]
    sport_vals = [r["sport_duration_min"] for r in rows]
    food_vals = [r["food_health_score"] for r in rows]
    sleep_quality_vals = [r["sleep_quality_score"] for r in rows]
    sleep_hours_vals = [r["sleep_hours"] for r in rows]

    h_trend = calc_trend(health_scores)
    w_trend = calc_trend(water_vals)
    s_trend = calc_trend(sport_vals)
    f_trend = calc_trend(food_vals)
    sl_trend = calc_trend(sleep_quality_vals)

    overall = generate_assessment(days, h_trend, s_trend, w_trend, sl_trend, f_trend)

    return success(
        {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "days": days,
            "health_score": {
                "current": round(health_scores[-1], 1),
                "avg": round(np.mean(health_scores), 1),
                "trend": h_trend,
            },
            "water": {
                "avg_ml": round(np.mean(water_vals), 1),
                "trend": w_trend,
            },
            "sport": {
                "total_min": int(sum(sport_vals)),
                "trend": s_trend,
            },
            "sleep": {
                "avg_hours": round(np.mean(sleep_hours_vals), 1),
                "avg_quality": round(np.mean(sleep_quality_vals), 1),
                "trend": sl_trend,
            },
            "food": {
                "avg_food_score": round(np.mean(food_vals), 1),
                "trend": f_trend,
            },
            "overall_assessment": overall,
        }
    )
