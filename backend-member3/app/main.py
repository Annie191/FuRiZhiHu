from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import Settings
from .errors import install_error_handlers
from .routers import auth, foods, health, profile, records


class BodyLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1_000_000:
            return JSONResponse(status_code=413, content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body is too large.", "details": None}})
        return await call_next(request)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    settings.ensure_runtime_requirements()
    app = FastAPI(title="FuCare API", docs_url="/docs", redoc_url=None)
    install_error_handlers(app)
    app.add_middleware(BodyLimitMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=[settings.cors_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    prefix = "/api/v1"
    app.include_router(health.router(settings), prefix=prefix)
    app.include_router(auth.router(settings), prefix=prefix)
    app.include_router(foods.router(settings), prefix=prefix)
    app.include_router(profile.router(settings), prefix=prefix)
    app.include_router(records.router(settings), prefix=prefix)

    @app.get("/")
    def root():
        return {"service": "fucare-api"}

    return app


app = create_app()
