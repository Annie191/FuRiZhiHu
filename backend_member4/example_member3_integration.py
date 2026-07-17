"""使用成员 3 JWT 健康管理接口生成一份成员 4 每日计划。"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date

from .api_client import Member3HealthApiClient
from .engine.planner import Planner


def main() -> None:
    """读取命令行天气参数并输出 JSON 计划。"""
    parser = argparse.ArgumentParser(description="调用成员3接口并生成成员4健康计划")
    parser.add_argument("--date", default=date.today().isoformat(), help="计划日期 YYYY-MM-DD")
    parser.add_argument("--city", default="上海")
    parser.add_argument("--temperature", type=float, default=36)
    parser.add_argument("--humidity", type=float, default=75)
    parser.add_argument("--aqi", type=float, default=80)
    parser.add_argument("--uv", type=float, default=7)
    arguments = parser.parse_args()

    token = os.environ.get("FUCARE_ACCESS_TOKEN")
    if not token:
        parser.error("请先设置 FUCARE_ACCESS_TOKEN，脚本不会读取或保存用户密码。")
    base_url = os.environ.get("FUCARE_API_BASE_URL", "http://127.0.0.1:3000/api/v1")
    client = Member3HealthApiClient(base_url, token, timeout_seconds=5)
    context = client.fetch_recommendation_context(arguments.date)
    weather = {
        "city": arguments.city,
        "temperature_c": arguments.temperature,
        "humidity_pct": arguments.humidity,
        "air_quality_index": arguments.aqi,
        "uv_index": arguments.uv,
    }
    result = Planner().compose_plan(context.profile, context.metrics, weather, context.date)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
