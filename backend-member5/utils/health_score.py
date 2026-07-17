"""健康指数 → 等级"""


def get_grade(score: float) -> str:
    """将 0-100 的健康指数转为中文等级"""
    if score >= 90:
        return "优秀"
    elif score >= 80:
        return "良好"
    elif score >= 60:
        return "一般"
    else:
        return "需改善"
