# 成员5 · 健康报告与趋势分析

FastAPI 实现的健康数据分析服务，负责健康报告、Dashboard 概览、趋势分析。**无鉴权**，由成员3 网关统一鉴权后内部调用。

> 用户画像、饮食/运动/睡眠记录 CRUD 由成员3 负责，本模块**不做重复实现**。

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
  report_router     B1/B2     健康报告
  statistics_router C4        综合概览
  trend_router      D1/D2     趋势分析

services/          # 业务逻辑
  trend_analyzer    numpy 线性回归 + 综合评语生成

utils/
  health_score.py   健康指数 → 等级

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

## API 总览（5 个接口）

| # | 方法 | 路径 | 说明 |
|---|------|------|------|
| B1 | GET | `/api/report/{user_id}/daily` | 每日健康报告 |
| B2 | GET | `/api/report/{user_id}/weekly` | 每周健康报告 |
| C4 | GET | `/api/statistics/{user_id}/overview` | Dashboard 概览 |
| D1 | GET | `/api/trend/{user_id}/health-score` | 健康指数趋势 |
| D2 | GET | `/api/trend/{user_id}/summary` | 综合趋势总结 |

详细文档见 `docs/api/`。

## 错误码

| code | 含义 |
|------|------|
| 0 | 成功 |
| 1001 | 用户画像不存在 |
