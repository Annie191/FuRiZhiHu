"""伏日智护（FuCare）成员5 后端 — FastAPI 入口"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from routers import report_router, statistics_router, trend_router

app = FastAPI(
    title="伏日智护 · 成员5 画像分析 API",
    version="2.0.0",
    description="健康报告、综合概览、趋势分析 — SQLite 视图优先",
)

# ── 统一参数校验错误格式（Pydantic 422 → 我们的 {code, msg, data}）─────────


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 提取第一个校验失败的字段和原因
    errors = exc.errors()
    if errors:
        err = errors[0]
        field = ".".join(str(loc) for loc in err["loc"] if loc != "body")
        msg = f"参数校验失败：{field} — {err['msg']}"
    else:
        msg = "参数校验失败"
    return JSONResponse(status_code=422, content={"code": 1002, "msg": msg, "data": None})


app.include_router(report_router.router, prefix="/api")
app.include_router(statistics_router.router, prefix="/api")
app.include_router(trend_router.router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "伏日智护 · 成员5 画像分析 API",
        "version": "2.0.0",
        "docs": "/docs",
    }
