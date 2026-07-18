# 成员 4：健康评分、天气风险与每日推荐

本目录只包含成员 4 负责的推荐逻辑，不修改成员 3 的 Express 源码。模块通过成员 3 已有 JWT 健康管理接口读取画像与每日汇总，再生成健康任务完成分、天气风险和四时段建议。

> 本项目用于课程演示，不构成医疗诊断或个体化处方。出现意识异常、昏厥等高温危险症状时应立即呼叫急救。

## 目录

```text
backend_member4/
├─ api_client.py                    # 成员 3 HTTP 接口客户端
├─ repository.py                    # weather_daily / daily_plan UPSERT
├─ config/
│  ├─ scoring_config.json           # 30/25/25/20 评分配置
│  └─ sanfu_periods.json            # 2026 年三伏日期
├─ engine/
│  ├─ health_scorer.py              # 与 SQL 视图一致的任务完成分
│  ├─ weather_processor.py          # 天气标准化、三伏与风险分级
│  ├─ rule_engine.py                # 经校验的 JSON 规则引擎
│  └─ planner.py                    # 纯计划生成器
├─ rules/sanfu_rules.json           # 推荐与运动限制规则
├─ tests/                           # 纯英文测试方法名
└─ example_member3_integration.py   # 手工联调示例
```

模块仅使用 Python 标准库，建议 Python 3.10 或更高版本。

## 评分口径

健康分表示“今日任务完成分”，与 `database/03_views_and_queries.sql` 中的 Dashboard 公式一致：

```text
健康分 = 饮水完成度 × 30%
       + 运动完成度 × 25%
       + 饮食健康度 × 25%
       + 睡眠质量   × 20%
```

- 饮水完成度：`water_ml / water_target_ml`，上限 100。
- 运动完成度：`sport_duration_min / 30`，上限 100。
- 饮食健康度：直接使用成员 3 `foodHealthScore`。
- 睡眠质量：直接使用成员 3 `sleepQualityScore`。
- 天气风险单独返回，不扣健康分。
- 负数、越界值、NaN 和 Infinity 会被明确拒绝。

## 调用成员 3 接口

客户端使用同一个登录 JWT 调用：

```text
GET /api/v1/auth/me
GET /api/v1/food-records/daily-summary?date=YYYY-MM-DD
GET /api/v1/water-records/daily-summary?date=YYYY-MM-DD
GET /api/v1/sport-records/daily-summary?date=YYYY-MM-DD
GET /api/v1/sleep-records/daily-summary?date=YYYY-MM-DD
```

示例：

```python
from backend_member4 import Member3HealthApiClient, Planner

client = Member3HealthApiClient(
    base_url="http://127.0.0.1:3000/api/v1",
    access_token=access_token,
    timeout_seconds=5,
)
context = client.fetch_recommendation_context("2026-07-17")

weather = {
    "city": "上海",
    "temperature_c": 36,
    "humidity_pct": 75,
    "air_quality_index": 80,
    "uv_index": 7,
}
result = Planner().compose_plan(
    user_profile=context.profile,
    metrics=context.metrics,
    weather=weather,
    plan_date=context.date,
)
```

指定日期没有汇总记录时，相应评分指标为 0，同时保留 `has_*_record=False`。没有睡眠记录不会误触发“睡眠不足”规则。

客户端异常：

| 异常 | 场景 |
|---|---|
| `AuthenticationError` | JWT 无效或过期 |
| `UpstreamValidationError` | 成员 3 拒绝日期等请求参数 |
| `UpstreamUnavailableError` | 连接失败或超时 |
| `UpstreamServiceError` | 成员 3 返回 5xx |
| `UpstreamProtocolError` | JSON 或字段结构不符合约定 |

JWT 只通过构造参数传入，不写入源码、配置或异常文本。

## 天气与三伏

`WeatherProcessor` 校验温度、湿度、AQI 和紫外线，输出：

- `risk_level`：`low` / `medium` / `high` / `extreme`
- `risk_factors`
- `advice`
- `is_sanfu` / `sanfu_stage` / `sanfu_known`
- `normalized_weather`

2026 年三伏配置：

- 初伏：7 月 15–24 日
- 中伏：7 月 25 日–8 月 13 日
- 末伏：8 月 14–23 日

未配置年份返回 `sanfu_known=False`，不会静默假装已判断。

## 保存结果

计划生成与数据库写入已分离：

```python
from backend_member4 import RecommendationRepository

repository = RecommendationRepository("database/furicare.db")
weather_id = repository.upsert_weather(result["weather_assessment"])
plan_id = repository.upsert_plan(
    user_id=context.profile["user_id"],
    plan_date=context.date,
    result=result,
    health_target_score=80,
)
```

Repository 使用 SQLite `ON CONFLICT DO UPDATE`，重复保存不会删除原行或改变 `plan_id` / `weather_id`。失败时抛出 `PersistenceError`，不会静默成功。

## 测试

在项目根目录运行：

```powershell
python -m compileall -q backend_member4
python -m unittest discover backend_member4/tests -v
python -m unittest database/test_database_usage.py -v
```

全部 Python 测试方法使用英文 ASCII `snake_case`；中文说明保留在 docstring 和断言消息中。`test_naming.py` 会自动阻止中文测试方法名进入提交。

## 手工联调

先启动成员 3 Express 服务并获得登录 JWT，然后在项目根目录运行：

```powershell
$env:FUCARE_ACCESS_TOKEN = "<登录返回的 accessToken>"
python -m backend_member4.example_member3_integration --date 2026-07-17
```

可通过 `FUCARE_API_BASE_URL` 修改接口地址，默认值为 `http://127.0.0.1:3000/api/v1`。示例只读取接口和生成计划，不写数据库。
