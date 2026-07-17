"""趋势分析：numpy 线性回归 + 综合评语"""

import numpy as np


def calc_trend(values: list) -> str:
    """对数值序列做线性回归，返回趋势方向"""
    if len(values) < 2:
        return "数据不足"
    x = np.arange(len(values))
    y = np.array(values, dtype=float)
    slope, _ = np.polyfit(x, y, 1)
    if slope > 0.5:
        return "上升"
    elif slope < -0.5:
        return "下降"
    else:
        return "平稳"


def generate_assessment(
    days: int,
    health_trend: str,
    sport_trend: str,
    water_trend: str,
    sleep_trend: str,
    food_trend: str,
) -> str:
    """根据各维度趋势生成综合自然语言评语"""
    parts = []

    # 健康总评
    if health_trend == "上升":
        parts.append(f"近{days}天健康状态整体向好")
    elif health_trend == "下降":
        parts.append(f"近{days}天健康状态有所下滑")
    else:
        parts.append(f"近{days}天健康状态保持平稳")

    # 改善的维度
    improved = []
    if sport_trend == "上升":
        improved.append("运动习惯明显改善")
    if water_trend == "上升":
        improved.append("饮水习惯有所进步")
    if food_trend == "上升":
        improved.append("饮食健康度稳步提升")
    if sleep_trend == "上升":
        improved.append("睡眠质量持续好转")
    parts.extend(improved)

    # 需关注的维度
    concerns = []
    if sleep_trend == "下降":
        concerns.append("睡眠质量")
    if food_trend == "下降":
        concerns.append("饮食健康度")
    if sport_trend == "下降":
        concerns.append("运动量")
    if water_trend == "下降":
        concerns.append("饮水量")
    if concerns:
        parts.append("需重点关注：" + "、".join(concerns))

    return "。".join(parts) + "。"
