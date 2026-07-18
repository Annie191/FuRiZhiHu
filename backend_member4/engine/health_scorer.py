"""与数据库 Dashboard 视图保持一致的健康任务完成分。"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping


_CONFIG_PATH = Path(__file__).parent.parent / "config" / "scoring_config.json"


class ScoreValidationError(ValueError):
    """评分输入不符合约定。"""


def load_config(path: Path = _CONFIG_PATH) -> dict[str, Any]:
    """读取并校验评分配置。"""
    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    weights = config.get("weights")
    if not isinstance(weights, dict) or set(weights) != {"water", "sport", "food", "sleep"}:
        raise ScoreValidationError("评分权重必须包含 water、sport、food、sleep。")
    numeric_weights = [_finite_number(weights[key], f"weights.{key}") for key in weights]
    if any(value < 0 for value in numeric_weights) or not math.isclose(sum(numeric_weights), 1.0, abs_tol=1e-9):
        raise ScoreValidationError("评分权重必须为非负数且总和等于 1。")
    _positive_number(config.get("sport_target_min"), "sport_target_min")
    return config


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ScoreValidationError(f"{field} 必须是有限数字。")
    return float(value)


def _non_negative_number(value: Any, field: str) -> float:
    number = _finite_number(value, field)
    if number < 0:
        raise ScoreValidationError(f"{field} 不能小于 0。")
    return number


def _positive_number(value: Any, field: str) -> float:
    number = _finite_number(value, field)
    if number <= 0:
        raise ScoreValidationError(f"{field} 必须大于 0。")
    return number


def _bounded_score(value: Any, field: str) -> float:
    number = _finite_number(value, field)
    if not 0 <= number <= 100:
        raise ScoreValidationError(f"{field} 必须在 0 到 100 之间。")
    return number


def _completion_value(actual: float, target: float) -> float:
    return max(0.0, min(actual / target, 1.0)) * 100.0


class HealthScorer:
    """根据数据库聚合指标计算 0-100 的今日任务完成分。"""

    def __init__(self, config: Mapping[str, Any] | None = None):
        self.config = dict(config) if config is not None else load_config()
        if config is not None:
            weights = self.config.get("weights", {})
            values = [_finite_number(weights.get(key), f"weights.{key}") for key in ("water", "sport", "food", "sleep")]
            if any(value < 0 for value in values) or not math.isclose(sum(values), 1.0, abs_tol=1e-9):
                raise ScoreValidationError("评分权重必须为非负数且总和等于 1。")
            _positive_number(self.config.get("sport_target_min"), "sport_target_min")

    def compute(
        self,
        profile: Mapping[str, Any],
        metrics: Mapping[str, Any],
        weather: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """计算健康分；weather 仅为兼容参数，不参与扣分。"""
        if not isinstance(profile, Mapping) or not isinstance(metrics, Mapping):
            raise ScoreValidationError("profile 和 metrics 必须是映射对象。")

        water_target = _positive_number(profile.get("water_target_ml"), "profile.water_target_ml")
        if not 500 <= water_target <= 6000:
            raise ScoreValidationError("profile.water_target_ml 必须在 500 到 6000 之间。")
        water_ml = _non_negative_number(metrics.get("water_ml"), "metrics.water_ml")
        sport_minutes = _non_negative_number(metrics.get("sport_duration_min"), "metrics.sport_duration_min")
        food_score = _bounded_score(metrics.get("food_health_score"), "metrics.food_health_score")
        sleep_score = _bounded_score(metrics.get("sleep_quality_score"), "metrics.sleep_quality_score")
        sport_target = _positive_number(self.config["sport_target_min"], "sport_target_min")

        raw_scores = {
            "water": _completion_value(water_ml, water_target),
            "sport": _completion_value(sport_minutes, sport_target),
            "food": food_score,
            "sleep": sleep_score,
        }
        sub_scores = {key: round(value, 2) for key, value in raw_scores.items()}
        weights = self.config["weights"]
        health_score = round(
            sum(raw_scores[key] * float(weights[key]) for key in raw_scores),
            2,
        )
        health_score = max(0.0, min(health_score, 100.0))

        return {
            "algorithm_version": self.config.get("algorithm_version", "1.0"),
            "health_score": health_score,
            "final_score": health_score,
            "sub_scores": sub_scores,
            "base_score": health_score,
            "env_penalty": 0.0,
            "details": {
                "water_target_ml": water_target,
                "water_ml": water_ml,
                "sport_target_min": sport_target,
                "sport_duration_min": sport_minutes,
                "food_health_score": food_score,
                "sleep_quality_score": sleep_score,
                "weather_affects_score": False,
            },
        }
