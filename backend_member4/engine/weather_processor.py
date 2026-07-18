"""天气数据校验、三伏日期识别和环境风险评估。"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Any, Mapping


_SANFU_PATH = Path(__file__).parent.parent / "config" / "sanfu_periods.json"


class WeatherValidationError(ValueError):
    """天气输入或三伏配置无效。"""


def _number(value: Any, field: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise WeatherValidationError(f"{field} 必须是有限数字。")
    number = float(value)
    if not minimum <= number <= maximum:
        raise WeatherValidationError(f"{field} 必须在 {minimum} 到 {maximum} 之间。")
    return number


def _parse_date(value: str) -> date:
    if not isinstance(value, str):
        raise WeatherValidationError("plan_date 必须是 YYYY-MM-DD 字符串。")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise WeatherValidationError("plan_date 必须是有效的 YYYY-MM-DD 日期。") from error
    if parsed.isoformat() != value:
        raise WeatherValidationError("plan_date 必须是 YYYY-MM-DD 格式。")
    return parsed


class WeatherProcessor:
    """把天气输入转换成独立于健康分的风险评估。"""

    def __init__(self, periods_path: str | Path = _SANFU_PATH):
        path = Path(periods_path)
        with path.open("r", encoding="utf-8") as file:
            self.periods = json.load(file)
        if not isinstance(self.periods, dict):
            raise WeatherValidationError("三伏配置必须是对象。")

    def process(self, weather: Mapping[str, Any], plan_date: str) -> dict[str, Any]:
        if not isinstance(weather, Mapping):
            raise WeatherValidationError("weather 必须是映射对象。")
        target_date = _parse_date(plan_date)
        temperature = _number(weather.get("temperature_c"), "temperature_c", -80, 60)
        humidity = _number(weather.get("humidity_pct"), "humidity_pct", 0, 100)
        aqi = _number(weather.get("air_quality_index", 0), "air_quality_index", 0, 1000)
        uv = _number(weather.get("uv_index", 0), "uv_index", 0, 30)
        city = weather.get("city")
        if city is not None and (not isinstance(city, str) or not city.strip()):
            raise WeatherValidationError("city 必须是非空字符串。")

        derived_stage, sanfu_known = self._sanfu_stage(target_date)
        explicit_sanfu = weather.get("is_sanfu")
        if explicit_sanfu is not None and not isinstance(explicit_sanfu, bool):
            raise WeatherValidationError("is_sanfu 必须是布尔值。")
        is_sanfu = explicit_sanfu if explicit_sanfu is not None else derived_stage is not None
        sanfu_stage = derived_stage if is_sanfu else None

        heat_extreme = temperature >= 41 or (temperature >= 38 and humidity >= 80)
        heat_high = temperature >= 35 or (temperature >= 33 and humidity >= 70)
        factors: list[str] = []
        advice: list[str] = []
        if heat_extreme:
            factors.append("extreme_heat")
            advice.append("高温危险，暂停高强度活动并尽量停留在凉爽环境。")
        elif heat_high:
            factors.append("high_heat")
            advice.append("天气炎热，避免 10:00-16:00 长时间户外活动。")
        elif temperature >= 33:
            factors.append("warm_weather")
            advice.append("天气偏热，注意通风、遮阳和适时休息。")
        if humidity >= 70:
            factors.append("high_humidity")
        if aqi >= 151:
            factors.append("poor_air_quality")
            advice.append("空气质量较差，建议选择室内活动。")
        elif aqi >= 101:
            factors.append("elevated_air_quality_index")
            advice.append("敏感人群应减少长时间户外活动。")
        if uv >= 8:
            factors.append("very_high_uv")
            advice.append("紫外线很强，外出请做好遮阳和防晒。")
        elif uv >= 6:
            factors.append("high_uv")
        if is_sanfu:
            factors.append("sanfu")

        if heat_extreme:
            risk_level = "extreme"
        elif heat_high or aqi >= 151 or uv >= 8:
            risk_level = "high"
        elif temperature >= 33 or humidity >= 70 or aqi >= 101 or uv >= 6:
            risk_level = "medium"
        else:
            risk_level = "low"
        if not advice:
            advice.append("环境风险较低，按个人计划安排活动并保持规律补水。")

        normalized = {
            "city": city.strip() if isinstance(city, str) else None,
            "weather_date": target_date.isoformat(),
            "temperature_c": temperature,
            "humidity_pct": humidity,
            "air_quality_index": aqi,
            "uv_index": uv,
            "is_sanfu": is_sanfu,
        }
        return {
            "risk_level": risk_level,
            "heat_risk": risk_level,
            "risk_factors": factors,
            "advice": advice,
            "is_sanfu": is_sanfu,
            "sanfu_stage": sanfu_stage,
            "sanfu_known": sanfu_known or explicit_sanfu is not None,
            "normalized_weather": normalized,
        }

    def _sanfu_stage(self, target_date: date) -> tuple[str | None, bool]:
        year_periods = self.periods.get(str(target_date.year))
        if year_periods is None:
            return None, False
        if not isinstance(year_periods, dict):
            raise WeatherValidationError(f"{target_date.year} 年三伏配置必须是对象。")
        for stage, bounds in year_periods.items():
            if not isinstance(bounds, list) or len(bounds) != 2:
                raise WeatherValidationError(f"{stage} 必须配置起止日期。")
            start, end = (_parse_date(value) for value in bounds)
            if start <= target_date <= end:
                return stage, True
        return None, True
