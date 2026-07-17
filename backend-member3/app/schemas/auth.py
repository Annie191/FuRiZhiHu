from __future__ import annotations

import re

from pydantic import EmailStr, Field, field_validator

from .common import StrictModel

PHONE_RE = re.compile(r"^1[3-9]\d{9}$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")


class ProfileInput(StrictModel):
    age: int = Field(ge=10, le=100)
    gender: str = Field(pattern="^(male|female|other)$")
    height_cm: float = Field(ge=100, le=250, validation_alias="heightCm")
    weight_kg: float = Field(ge=20, le=300, validation_alias="weightKg")
    goal: str = Field(pattern="^(lose_fat|maintain|gain_muscle)$")
    activity_level: str = Field(pattern="^(low|medium|high)$", validation_alias="activityLevel")
    avg_sleep_hours: float = Field(ge=0, le=24, validation_alias="avgSleepHours")
    water_target_ml: int = Field(default=2200, ge=500, le=6000, validation_alias="waterTargetMl")
    profile_tag: str = Field(min_length=1, max_length=100, validation_alias="profileTag")

    @field_validator("profile_tag")
    @classmethod
    def trim_tag(cls, value: str) -> str:
        return value.strip()


class RegistrationInput(StrictModel):
    username: str
    password: str = Field(min_length=12, max_length=128)
    nickname: str = Field(min_length=1, max_length=50)
    phone: str | None = None
    email: EmailStr | None = None
    profile: ProfileInput

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str) -> str:
        value = value.strip()
        if not USERNAME_RE.fullmatch(value):
            raise ValueError("用户名需为 3-32 位字母、数字、下划线或连字符。")
        return value

    @field_validator("nickname")
    @classmethod
    def trim_nickname(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not PHONE_RE.fullmatch(value):
            raise ValueError("手机号格式不正确。")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr | None) -> str | None:
        return str(value).lower() if value else None


class LoginInput(StrictModel):
    identifier: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("identifier")
    @classmethod
    def trim_identifier(cls, value: str) -> str:
        return value.strip()
