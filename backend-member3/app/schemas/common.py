from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from ..errors import ApiError

StrictText = Annotated[str, StringConstraints(strip_whitespace=True)]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}$")


def valid_date(value: str) -> str:
    if not DATE_RE.fullmatch(value):
        raise ValueError("日期必须为 YYYY-MM-DD。")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as error:
        raise ValueError("日期必须为 YYYY-MM-DD。") from error
    return value


def valid_datetime(value: str) -> str:
    if not DATETIME_RE.fullmatch(value):
        raise ValueError("日期时间必须为 YYYY-MM-DD HH:MM:SS。")
    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError as error:
        raise ValueError("日期时间无效。") from error
    return value


def valid_time(value: str) -> str:
    if not TIME_RE.fullmatch(value):
        raise ValueError("时间必须为 HH:MM:SS。")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ListQuery(StrictModel):
    page: int = Field(default=1, ge=1, le=10000)
    page_size: int = Field(default=20, ge=1, le=100, validation_alias="pageSize", serialization_alias="pageSize")
    date: str | None = None
    from_date: str | None = Field(default=None, validation_alias="from")
    to: str | None = None

    def validate_range(self) -> None:
        for value in (self.date, self.from_date, self.to):
            if value is not None:
                valid_date(value)
        if self.date and (self.from_date or self.to):
            raise ApiError(400, "VALIDATION_ERROR", "Request validation failed.", [{"path": "date", "message": "date 不能与 from/to 同时使用。"}])
        if bool(self.from_date) != bool(self.to):
            raise ApiError(400, "VALIDATION_ERROR", "Request validation failed.", [{"path": "from", "message": "from 和 to 必须同时提供。"}])
        if self.from_date and self.to:
            days = (datetime.strptime(self.to, "%Y-%m-%d") - datetime.strptime(self.from_date, "%Y-%m-%d")).days
            if days < 0:
                raise ApiError(400, "VALIDATION_ERROR", "Request validation failed.", [{"path": "from", "message": "from 不能晚于 to。"}])
            if days > 366:
                raise ApiError(400, "VALIDATION_ERROR", "Request validation failed.", [{"path": "to", "message": "日期范围不能超过 366 天。"}])


def require_nonempty(model: BaseModel) -> None:
    if not model.model_fields_set:
        raise ApiError(400, "VALIDATION_ERROR", "Request body cannot be empty.")
