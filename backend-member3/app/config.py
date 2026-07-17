from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    app_env: str = Field(default="development", validation_alias="NODE_ENV")
    host: str = Field(default="127.0.0.1", validation_alias="HOST")
    port: int = Field(default=3000, validation_alias="PORT", ge=1, le=65535)
    database_path: str = Field(default="database/furicare.db", validation_alias="DATABASE_PATH")
    jwt_secret: str = Field(default="development-secret-at-least-16-chars", validation_alias="JWT_SECRET", min_length=16)
    jwt_expires_in: str = Field(default="7d", validation_alias="JWT_EXPIRES_IN")
    cors_origin: str = Field(default="http://localhost:5173", validation_alias="CORS_ORIGIN")

    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        if value not in {"development", "test", "production"}:
            raise ValueError("NODE_ENV must be development, test, or production.")
        return value

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("HOST cannot be empty.")
        return value

    @field_validator("jwt_expires_in")
    @classmethod
    def validate_expiry(cls, value: str) -> str:
        if len(value) < 2 or not value[:-1].isdigit() or value[-1] not in "smhdw":
            raise ValueError("JWT_EXPIRES_IN must use <number><s|m|h|d|w> format.")
        return value

    @property
    def resolved_database_path(self) -> Path:
        path = Path(self.database_path)
        return path if path.is_absolute() else PROJECT_ROOT / path

    def ensure_runtime_requirements(self) -> None:
        if not self.resolved_database_path.exists():
            raise RuntimeError(f"Database file does not exist: {self.resolved_database_path}")
        if self.app_env == "production" and self.jwt_secret == "change-this-to-a-long-random-secret":
            raise RuntimeError("JWT_SECRET must be changed in production.")
