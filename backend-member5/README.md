# 成员5 · 画像分析后端

FastAPI 实现的健康数据分析服务，负责用户画像、健康报告、数据统计、趋势分析。**无鉴权**，由成员3 网关统一鉴权后内部调用。

## 快速启动

```bash
cd backend-member5
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

启动后访问 `http://localhost:8000/docs` 查看 Swagger 文档。

## 依赖

| 包 | 用途 |
|---|------|
| fastapi + uvicorn | HTTP 服务 |
| numpy | D1/D2 趋势线性回归 |

数据库使用 Python 标准库 `sqlite3`，无需额外安装。数据库文件位于 `../database/furicare.db`。

## 架构

```
routers/           # 路由层 — 参数校验、SQL 查询、组装响应
  profile_router    A1/A2/A3  用户画像
  report_router     B1/B2     健康报告
  statistics_router C1~C4     数据统计
  trend_router      D1/D2     趋势分析

services/          # 业务逻辑
  profile_analyzer  标签规则 + 饮水目标计算
  trend_analyzer    numpy 线性回归 + 综合评语生成

utils/
  health_score.py   健康指数 → 等级

config.py           SQLite 连接 + 统一响应格式
main.py             FastAPI 入口 + Pydantic 校验异常处理
```

## 数据策略

**视图优先**：能查视图不手写 JOIN。成员2 已建的 5 个视图：

| 视图 | 用途 |
|------|------|
| `v_dashboard_daily` | 首页总览（健康指数已算好） |
| `v_daily_food_summary` | 每日饮食汇总 |
| `v_daily_water_summary` | 每日饮水汇总 |
| `v_daily_sport_summary` | 每日运动汇总 |
| `v_daily_sleep_summary` | 每日睡眠汇总 |

## API 总览（12 个接口）

| # | 方法 | 路径 | 说明 |
|---|------|------|------|
| A1 | POST | `/api/profile/analyze` | 生成用户画像 |
| A2 | GET | `/api/profile/{user_id}` | 查询用户画像 |
| A3 | PUT | `/api/profile/{user_id}` | 更新用户画像 |
| B1 | GET | `/api/report/{user_id}/daily` | 每日健康报告 |
| B2 | GET | `/api/report/{user_id}/weekly` | 每周健康报告 |
| C1 | GET | `/api/statistics/{user_id}/food` | 饮食统计 |
| C2 | GET | `/api/statistics/{user_id}/sport` | 运动统计 |
| C3 | GET | `/api/statistics/{user_id}/sleep` | 睡眠统计 |
| C4 | GET | `/api/statistics/{user_id}/overview` | Dashboard 概览 |
| D1 | GET | `/api/trend/{user_id}/health-score` | 健康指数趋势 |
| D2 | GET | `/api/trend/{user_id}/summary` | 综合趋势总结 |

详细文档见 `docs/api/`。

## 错误码

| code | 含义 |
|------|------|
| 0 | 成功 |
| 1001 | 用户画像不存在（或用户不存在） |
| 1002 | 参数校验失败 |
| 1003 | 用户账号不存在 |
