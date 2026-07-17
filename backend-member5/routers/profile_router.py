"""A 模块：用户画像 — A1 生成 / A2 查询 / A3 更新"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from config import get_db, success, fail
from services.profile_analyzer import get_profile_tag, calc_water_target

router = APIRouter()

# ── Pydantic 模型 ──────────────────────────────────────────────────────


class ProfileCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    age: int = Field(..., ge=10, le=100)
    gender: str = Field(..., pattern=r"^(male|female|other)$")
    height_cm: float = Field(..., ge=100, le=250)
    weight_kg: float = Field(..., ge=20, le=300)
    activity_level: str = Field(..., pattern=r"^(low|medium|high)$")
    avg_sleep_hours: float = Field(..., ge=0, le=24)
    goal: str = Field(..., pattern=r"^(lose_fat|maintain|gain_muscle)$")


class ProfileUpdate(BaseModel):
    age: int | None = Field(None, ge=10, le=100)
    gender: str | None = Field(None, pattern=r"^(male|female|other)$")
    height_cm: float | None = Field(None, ge=100, le=250)
    weight_kg: float | None = Field(None, ge=20, le=300)
    activity_level: str | None = Field(None, pattern=r"^(low|medium|high)$")
    avg_sleep_hours: float | None = Field(None, ge=0, le=24)
    goal: str | None = Field(None, pattern=r"^(lose_fat|maintain|gain_muscle)$")


# ── A1：生成用户画像 ────────────────────────────────────────────────────


@router.post("/profile/analyze")
def create_profile(body: ProfileCreate):
    db = get_db()
    data = body.model_dump()

    # 检查账号是否存在
    account = db.execute(
        "SELECT user_id FROM user_account WHERE user_id = ?", (data["user_id"],)
    ).fetchone()
    if not account:
        db.close()
        return fail("用户账号不存在，请先注册", code=1003)

    # 检查画像是否已存在
    existing = db.execute(
        "SELECT user_id FROM user_profile WHERE user_id = ?", (data["user_id"],)
    ).fetchone()
    if existing:
        db.close()
        return fail("用户画像已存在，请更新", code=1001)

    # 生成标签 & 饮水目标
    profile_tag = get_profile_tag(data["goal"], data["activity_level"])
    water_target = calc_water_target(data["height_cm"], data["weight_kg"], data["goal"])

    db.execute(
        """INSERT INTO user_profile
           (user_id, age, gender, height_cm, weight_kg, goal, activity_level,
            avg_sleep_hours, water_target_ml, profile_tag)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["user_id"],
            data["age"],
            data["gender"],
            data["height_cm"],
            data["weight_kg"],
            data["goal"],
            data["activity_level"],
            data["avg_sleep_hours"],
            water_target,
            profile_tag,
        ),
    )
    db.commit()

    # 读回（获取数据库自动计算的 bmi、created_at、updated_at）
    row = db.execute(
        """SELECT user_id, age, gender, height_cm, weight_kg, bmi,
                  goal, activity_level, avg_sleep_hours, profile_tag,
                  water_target_ml, created_at, updated_at
           FROM user_profile WHERE user_id = ?""",
        (data["user_id"],),
    ).fetchone()

    db.close()
    return success(dict(row))


# ── A2：查询用户画像 ────────────────────────────────────────────────────


@router.get("/profile/{user_id}")
def get_profile(user_id: int):
    db = get_db()

    row = db.execute(
        """SELECT ua.user_id, ua.nickname,
                  up.age, up.gender, up.height_cm, up.weight_kg, up.bmi,
                  up.goal, up.activity_level, up.avg_sleep_hours,
                  up.profile_tag, up.water_target_ml,
                  up.created_at, up.updated_at
           FROM user_account ua
           INNER JOIN user_profile up ON up.user_id = ua.user_id
           WHERE ua.user_id = ?""",
        (user_id,),
    ).fetchone()

    db.close()

    if not row:
        return fail("用户画像不存在，请先创建画像", code=1001)

    return success(dict(row))


# ── A3：更新用户画像 ────────────────────────────────────────────────────


@router.put("/profile/{user_id}")
def update_profile(user_id: int, body: ProfileUpdate):
    db = get_db()

    # 查现画像
    existing = db.execute(
        """SELECT up.*, ua.nickname
           FROM user_profile up
           JOIN user_account ua ON ua.user_id = up.user_id
           WHERE up.user_id = ?""",
        (user_id,),
    ).fetchone()

    if not existing:
        db.close()
        return fail("用户画像不存在，请先创建画像", code=1001)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        db.close()
        return success(dict(existing))

    # 合并：新值优先
    merged = dict(existing)
    merged.update(updates)

    # 如果 goal 或 activity_level 变了 → 重算标签
    if "goal" in updates or "activity_level" in updates:
        merged["profile_tag"] = get_profile_tag(merged["goal"], merged["activity_level"])

    # 如果体重/身高/goal 变了 → 重算饮水目标
    if any(k in updates for k in ("weight_kg", "height_cm", "goal")):
        merged["water_target_ml"] = calc_water_target(
            merged["height_cm"], merged["weight_kg"], merged["goal"]
        )

    db.execute(
        """UPDATE user_profile
           SET age=?, gender=?, height_cm=?, weight_kg=?, goal=?,
               activity_level=?, avg_sleep_hours=?, profile_tag=?,
               water_target_ml=?, updated_at=CURRENT_TIMESTAMP
           WHERE user_id=?""",
        (
            merged["age"],
            merged["gender"],
            merged["height_cm"],
            merged["weight_kg"],
            merged["goal"],
            merged["activity_level"],
            merged["avg_sleep_hours"],
            merged["profile_tag"],
            merged["water_target_ml"],
            user_id,
        ),
    )
    db.commit()

    # 读回更新后数据
    row = db.execute(
        """SELECT ua.user_id, ua.nickname,
                  up.age, up.gender, up.height_cm, up.weight_kg, up.bmi,
                  up.goal, up.activity_level, up.avg_sleep_hours,
                  up.profile_tag, up.water_target_ml,
                  up.created_at, up.updated_at
           FROM user_profile up
           JOIN user_account ua ON ua.user_id = up.user_id
           WHERE up.user_id = ?""",
        (user_id,),
    ).fetchone()

    db.close()
    return success(dict(row))
