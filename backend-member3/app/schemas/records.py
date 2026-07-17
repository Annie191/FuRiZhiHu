from __future__ import annotations

from pydantic import Field, field_validator

from .common import StrictModel, valid_date, valid_datetime, valid_time


class RecordBase(StrictModel):
    note: str | None = Field(default=None, max_length=500)

    @field_validator("note")
    @classmethod
    def trim_note(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class FoodRecordInput(RecordBase):
    food_id: int = Field(gt=0, validation_alias="foodId")
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$", validation_alias="mealType")
    amount: float = Field(gt=0, le=10000)
    amount_unit: str = Field(pattern="^(g|ml)$", validation_alias="amountUnit")
    intake_date: str = Field(validation_alias="intakeDate")

    _date = field_validator("intake_date")(valid_date)


class WaterRecordInput(RecordBase):
    amount_ml: int = Field(ge=50, le=3000, validation_alias="amountMl")
    source: str = Field(default="water", pattern="^(water|tea|soup|other)$")
    intake_time: str = Field(validation_alias="intakeTime")

    _datetime = field_validator("intake_time")(valid_datetime)


class SportRecordInput(RecordBase):
    sport_type: str = Field(min_length=1, max_length=50, validation_alias="sportType")
    intensity: str = Field(default="medium", pattern="^(low|medium|high)$")
    duration_min: int = Field(ge=1, le=1440, validation_alias="durationMin")
    calories_burned: float = Field(default=0, ge=0, le=20000, validation_alias="caloriesBurned")
    record_date: str = Field(validation_alias="recordDate")
    start_time: str | None = Field(default=None, validation_alias="startTime")

    _date = field_validator("record_date")(valid_date)
    _time = field_validator("start_time")(lambda value: valid_time(value) if value is not None else value)

    @field_validator("sport_type")
    @classmethod
    def trim_sport_type(cls, value: str) -> str:
        return value.strip()


class SleepRecordInput(RecordBase):
    sleep_time: str = Field(validation_alias="sleepTime")
    wake_time: str = Field(validation_alias="wakeTime")
    quality_score: int = Field(ge=0, le=100, validation_alias="qualityScore")
    record_date: str = Field(validation_alias="recordDate")

    _sleep = field_validator("sleep_time")(valid_datetime)
    _wake = field_validator("wake_time")(valid_datetime)
    _date = field_validator("record_date")(valid_date)
