"""用户画像分析：标签规则 + 饮水目标计算"""

# (goal, activity_level) → 中文标签
TAG_RULES = {
    ("lose_fat", "low"): "夏季减脂型",
    ("lose_fat", "medium"): "夏季减脂型",
    ("lose_fat", "high"): "夏季减脂活跃型",
    ("gain_muscle", "low"): "夏季增肌型",
    ("gain_muscle", "medium"): "夏季增肌型",
    ("gain_muscle", "high"): "夏季增肌活跃型",
    ("maintain", "low"): "夏季养生型",
    ("maintain", "medium"): "规律养生型",
    ("maintain", "high"): "夏季活力型",
}


def get_profile_tag(goal: str, activity_level: str) -> str:
    return TAG_RULES.get((goal, activity_level), "未分类")


def calc_water_target(height_cm: float, weight_kg: float, goal: str) -> int:
    """根据身高、体重、目标计算每日饮水目标（ml）"""
    height_m = height_cm / 100.0
    standard_weight = 22 * height_m * height_m

    water = 2000  # 基础饮水

    if weight_kg > standard_weight:
        water += int((weight_kg - standard_weight) // 10) * 200

    if goal == "lose_fat":
        water += 200  # 减脂额外补水

    water += 300  # 夏季高温加成

    # 夹在合理范围内
    return max(500, min(6000, water))
