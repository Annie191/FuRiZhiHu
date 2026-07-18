"""组合健康分、天气风险和规则建议的纯计划生成器。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .health_scorer import HealthScorer
from .rule_engine import RuleEngine
from .weather_processor import WeatherProcessor


_DEFAULT_RULES = Path(__file__).parent.parent / "rules" / "sanfu_rules.json"


class Planner:
    """生成确定性的每日健康计划，不在计算过程中写数据库。"""

    def __init__(
        self,
        rules_path: str | Path = _DEFAULT_RULES,
        scorer: HealthScorer | None = None,
        weather_processor: WeatherProcessor | None = None,
    ):
        with Path(rules_path).open("r", encoding="utf-8") as file:
            rules = json.load(file)
        self.rule_engine = RuleEngine(rules)
        self.scorer = scorer or HealthScorer()
        self.weather_processor = weather_processor or WeatherProcessor()

    def compose_plan(
        self,
        user_profile: Mapping[str, Any],
        metrics: Mapping[str, Any],
        weather: Mapping[str, Any],
        plan_date: str,
        as_of_time: datetime | None = None,
    ) -> dict[str, Any]:
        """根据画像、每日聚合指标和天气生成计划。"""
        score = self.scorer.compute(user_profile, metrics)
        assessment = self.weather_processor.process(weather, plan_date)
        if as_of_time is not None and not isinstance(as_of_time, datetime):
            raise ValueError("as_of_time 必须是 datetime 或 None。")
        now = as_of_time or datetime.now()
        context = {
            "user_profile": dict(user_profile),
            "metrics": dict(metrics),
            "weather": assessment["normalized_weather"],
            "weather_assessment": assessment,
            "is_sanfu": assessment["is_sanfu"],
            "sanfu_stage": assessment["sanfu_stage"],
            "current_hour": now.hour,
            "has_sleep_record": bool(metrics.get("has_sleep_record", True)),
        }
        actions = self.rule_engine.run(context)
        slots: dict[str, list[str]] = {
            "breakfast": [],
            "midday": [],
            "exercise": [],
            "evening": [],
        }
        veto: dict[str, Any] | None = None
        triggered_rule_ids: list[str] = []
        for item in actions:
            if item["rule_id"] not in triggered_rule_ids:
                triggered_rule_ids.append(item["rule_id"])
            action = item["action"]
            if action["type"] == "advice":
                slots[action["slot"]].append(action["text"])
            elif action["type"] == "veto" and veto is None:
                veto = {"rule_id": item["rule_id"], "reason": action["reason"]}

        plan = {
            "breakfast_advice": "\n".join(slots["breakfast"]) or "早餐选择清淡、均衡且易消化的食物。",
            "midday_advice": "\n".join(slots["midday"]) or "白天按个人饮水目标规律补水，并避免长时间暴晒。",
            "exercise_advice": "\n".join(slots["exercise"]) or "根据环境和身体状态安排适度活动。",
            "evening_advice": "\n".join(slots["evening"]) or "晚间适度放松，保持规律作息。",
        }
        return {
            "algorithm_version": score["algorithm_version"],
            "plan_date": plan_date,
            "health_score": score["health_score"],
            "sub_scores": score["sub_scores"],
            "score_detail": score,
            "weather_assessment": assessment,
            "plan": plan,
            "veto": veto,
            "triggered_rule_ids": triggered_rule_ids,
            "triggered_actions": actions,
        }
