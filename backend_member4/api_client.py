"""成员 3 Express 健康管理接口的标准库客户端。"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class Member3ApiError(RuntimeError):
    """成员 3 接口调用基础异常。"""


class AuthenticationError(Member3ApiError):
    """JWT 缺失、过期或无效。"""


class UpstreamValidationError(Member3ApiError):
    """成员 3 接口拒绝了请求参数。"""


class UpstreamUnavailableError(Member3ApiError):
    """成员 3 服务无法连接或请求超时。"""


class UpstreamServiceError(Member3ApiError):
    """成员 3 服务返回 5xx。"""


class UpstreamProtocolError(Member3ApiError):
    """成员 3 返回的数据不符合约定。"""


@dataclass(frozen=True)
class RecommendationContext:
    """成员 4 计划生成器所需的标准化输入。"""

    date: str
    profile: dict[str, Any]
    metrics: dict[str, Any]


class Member3HealthApiClient:
    """读取健康画像和四类每日汇总，不负责登录或保存 JWT。"""

    def __init__(self, base_url: str, access_token: str, timeout_seconds: float = 5):
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("base_url 不能为空。")
        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError("access_token 不能为空。")
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds 必须大于 0。")
        self.base_url = base_url.rstrip("/")
        self._access_token = access_token
        self.timeout_seconds = float(timeout_seconds)

    def fetch_recommendation_context(self, target_date: str) -> RecommendationContext:
        """调用五个接口并转换为成员 4 snake_case 数据结构。"""
        self._validate_date(target_date)
        current = self._get("/auth/me")
        user = self._require_mapping(current, "user")
        profile_data = self._require_mapping(user, "profile")
        profile = {
            "user_id": self._required_int(user, "id"),
            "age": self._required_number(profile_data, "age"),
            "gender": self._required_string(profile_data, "gender"),
            "height_cm": self._required_number(profile_data, "heightCm"),
            "weight_kg": self._required_number(profile_data, "weightKg"),
            "goal": self._required_string(profile_data, "goal"),
            "activity_level": self._required_string(profile_data, "activityLevel"),
            "avg_sleep_hours": self._required_number(profile_data, "avgSleepHours"),
            "water_target_ml": self._required_number(profile_data, "waterTargetMl"),
            "profile_tag": self._required_string(profile_data, "profileTag"),
        }

        query = urlencode({"date": target_date})
        food = self._get_daily_summary(f"/food-records/daily-summary?{query}", target_date)
        water = self._get_daily_summary(f"/water-records/daily-summary?{query}", target_date)
        sport = self._get_daily_summary(f"/sport-records/daily-summary?{query}", target_date)
        sleep = self._get_daily_summary(f"/sleep-records/daily-summary?{query}", target_date)
        metrics = {
            "water_ml": self._optional_number(water, "totalWaterMl", 0),
            "sport_duration_min": self._optional_number(sport, "totalDurationMin", 0),
            "food_health_score": self._optional_number(food, "foodHealthScore", 0),
            "sleep_hours": self._optional_number(sleep, "sleepHours", 0),
            "sleep_quality_score": self._optional_number(sleep, "sleepQualityScore", 0),
            "has_water_record": water is not None,
            "has_sport_record": sport is not None,
            "has_food_record": food is not None,
            "has_sleep_record": sleep is not None,
        }
        return RecommendationContext(date=target_date, profile=profile, metrics=metrics)

    def _get(self, path: str) -> Any:
        request = Request(
            f"{self.base_url}{path}",
            headers={"Authorization": f"Bearer {self._access_token}", "Accept": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as error:
            if error.code == 401:
                raise AuthenticationError("成员3接口认证失败。") from error
            if error.code == 400:
                raise UpstreamValidationError("成员3接口拒绝了请求参数。") from error
            if 500 <= error.code:
                raise UpstreamServiceError("成员3服务暂时异常。") from error
            raise Member3ApiError(f"成员3接口返回 HTTP {error.code}。") from error
        except (URLError, TimeoutError, socket.timeout, OSError) as error:
            raise UpstreamUnavailableError("无法连接成员3健康管理服务。") from error
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise UpstreamProtocolError("成员3接口返回了无效 JSON。") from error
        if not isinstance(payload, dict) or "data" not in payload:
            raise UpstreamProtocolError("成员3接口响应缺少 data 字段。")
        return payload["data"]

    def _get_daily_summary(self, path: str, target_date: str) -> dict[str, Any] | None:
        data = self._get(path)
        if not isinstance(data, list) or len(data) > 1:
            raise UpstreamProtocolError("指定日期的 daily-summary 必须返回零或一项。")
        if not data:
            return None
        row = data[0]
        if not isinstance(row, dict) or row.get("date") != target_date:
            raise UpstreamProtocolError("daily-summary 日期或结构不符合约定。")
        return row

    @staticmethod
    def _validate_date(value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("日期必须是 YYYY-MM-DD 字符串。")
        try:
            parsed = date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("日期必须是有效的 YYYY-MM-DD。") from error
        if parsed.isoformat() != value:
            raise ValueError("日期必须是 YYYY-MM-DD 格式。")

    @staticmethod
    def _require_mapping(value: Any, key: str) -> dict[str, Any]:
        if not isinstance(value, dict) or not isinstance(value.get(key), dict):
            raise UpstreamProtocolError(f"成员3响应缺少对象字段 {key}。")
        return value[key]

    @staticmethod
    def _required_number(value: dict[str, Any], key: str) -> float:
        item = value.get(key)
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise UpstreamProtocolError(f"成员3响应字段 {key} 必须是数字。")
        return item

    @staticmethod
    def _required_int(value: dict[str, Any], key: str) -> int:
        item = value.get(key)
        if isinstance(item, bool) or not isinstance(item, int):
            raise UpstreamProtocolError(f"成员3响应字段 {key} 必须是整数。")
        return item

    @staticmethod
    def _required_string(value: dict[str, Any], key: str) -> str:
        item = value.get(key)
        if not isinstance(item, str):
            raise UpstreamProtocolError(f"成员3响应字段 {key} 必须是字符串。")
        return item

    @staticmethod
    def _optional_number(value: dict[str, Any] | None, key: str, default: float) -> float:
        if value is None:
            return default
        return Member3HealthApiClient._required_number(value, key)
