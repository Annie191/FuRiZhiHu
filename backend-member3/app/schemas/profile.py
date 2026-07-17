from __future__ import annotations

from pydantic import Field

from .auth import ProfileInput


class ProfilePatch(ProfileInput):
    age: int | None = Field(default=None, ge=10, le=100)
    gender: str | None = Field(default=None, pattern="^(male|female|other)$")
    height_cm: float | None = Field(default=None, ge=100, le=250, validation_alias="heightCm")
    weight_kg: float | None = Field(default=None, ge=20, le=300, validation_alias="weightKg")
    goal: str | None = Field(default=None, pattern="^(lose_fat|maintain|gain_muscle)$")
    activity_level: str | None = Field(default=None, pattern="^(low|medium|high)$", validation_alias="activityLevel")
    avg_sleep_hours: float | None = Field(default=None, ge=0, le=24, validation_alias="avgSleepHours")
    water_target_ml: int | None = Field(default=None, ge=500, le=6000, validation_alias="waterTargetMl")
    profile_tag: str | None = Field(default=None, min_length=1, max_length=100, validation_alias="profileTag")
