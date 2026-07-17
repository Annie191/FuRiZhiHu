import unittest
from datetime import datetime

from backend_member4.engine.planner import Planner


class TestPlanner(unittest.TestCase):
    """每日计划组合测试。"""

    def setUp(self):
        """初始化标准画像、聚合指标和三伏天气。"""
        self.planner = Planner()
        self.profile = {
            "user_id": 1,
            "age": 25,
            "gender": "male",
            "height_cm": 175,
            "weight_kg": 70,
            "goal": "lose_fat",
            "activity_level": "low",
            "avg_sleep_hours": 7,
            "water_target_ml": 2200,
        }
        self.metrics = {
            "water_ml": 1500,
            "sport_duration_min": 10,
            "food_health_score": 75,
            "sleep_hours": 6.5,
            "sleep_quality_score": 80,
            "has_water_record": True,
            "has_sport_record": True,
            "has_food_record": True,
            "has_sleep_record": True,
        }
        self.weather = {
            "city": "上海",
            "temperature_c": 36,
            "humidity_pct": 75,
            "air_quality_index": 80,
            "uv_index": 7,
        }

    def test_plan_contains_required_output_fields(self):
        """计划结果应包含评分、天气、建议和触发规则。"""
        result = self.planner.compose_plan(self.profile, self.metrics, self.weather, "2026-07-17")
        for field in ("algorithm_version", "health_score", "sub_scores", "weather_assessment", "plan", "veto", "triggered_rule_ids"):
            self.assertIn(field, result, f"计划结果缺少 {field}")

    def test_plan_contains_four_non_empty_advice_slots(self):
        """四个时段都必须返回非空建议。"""
        result = self.planner.compose_plan(self.profile, self.metrics, self.weather, "2026-07-17")
        expected = {"breakfast_advice", "midday_advice", "exercise_advice", "evening_advice"}
        self.assertEqual(set(result["plan"]), expected)
        for slot, text in result["plan"].items():
            self.assertTrue(text.strip(), f"{slot} 不应为空")

    def test_sanfu_high_temperature_rule_is_triggered(self):
        """三伏高温应触发户外运动调整规则。"""
        result = self.planner.compose_plan(self.profile, self.metrics, self.weather, "2026-07-17")
        self.assertIn("sanfu_reduce_outdoor_high_temperature", result["triggered_rule_ids"])
        self.assertEqual(result["weather_assessment"]["sanfu_stage"], "初伏")

    def test_extreme_heat_produces_single_veto(self):
        """极端高温应产生一个且仅一个明确 veto。"""
        weather = dict(self.weather, temperature_c=41)
        result = self.planner.compose_plan(self.profile, self.metrics, weather, "2026-07-17")
        veto_actions = [item for item in result["triggered_actions"] if item["action"]["type"] == "veto"]
        self.assertEqual(len(veto_actions), 1, "极端高温只能产生一个 veto")
        self.assertIn("暂停高强度活动", result["veto"]["reason"])

    def test_missing_sleep_record_does_not_trigger_sleep_deficit(self):
        """没有睡眠记录时不得把未知误判为睡眠不足。"""
        metrics = dict(self.metrics, sleep_hours=0, sleep_quality_score=0, has_sleep_record=False)
        result = self.planner.compose_plan(self.profile, metrics, self.weather, "2026-07-17")
        self.assertNotIn("sleep_deficit_reduce_exertion", result["triggered_rule_ids"])

    def test_short_sleep_record_triggers_sleep_deficit(self):
        """实际睡眠少于 6 小时时应降低运动强度。"""
        metrics = dict(self.metrics, sleep_hours=5.5, has_sleep_record=True)
        result = self.planner.compose_plan(self.profile, metrics, self.weather, "2026-07-17")
        self.assertIn("sleep_deficit_reduce_exertion", result["triggered_rule_ids"])

    def test_morning_does_not_trigger_daily_water_progress_alert(self):
        """上午不得用全天 50% 目标误报饮水不足。"""
        metrics = dict(self.metrics, water_ml=100)
        result = self.planner.compose_plan(
            self.profile,
            metrics,
            self.weather,
            "2026-07-17",
            as_of_time=datetime(2026, 7, 17, 9, 0),
        )
        self.assertNotIn("low_water_progress_alert", result["triggered_rule_ids"])

    def test_afternoon_triggers_daily_water_progress_alert(self):
        """下午仍低于目标一半时应提醒补水。"""
        metrics = dict(self.metrics, water_ml=100)
        result = self.planner.compose_plan(
            self.profile,
            metrics,
            self.weather,
            "2026-07-17",
            as_of_time=datetime(2026, 7, 17, 15, 0),
        )
        self.assertIn("low_water_progress_alert", result["triggered_rule_ids"])

    def test_weather_risk_does_not_change_health_score(self):
        """天气风险变化只能改变建议，不能改变健康分。"""
        normal = dict(self.weather, temperature_c=25, humidity_pct=50)
        extreme = dict(self.weather, temperature_c=41)
        normal_result = self.planner.compose_plan(self.profile, self.metrics, normal, "2026-07-17")
        extreme_result = self.planner.compose_plan(self.profile, self.metrics, extreme, "2026-07-17")
        self.assertEqual(normal_result["health_score"], extreme_result["health_score"])
        self.assertNotEqual(normal_result["weather_assessment"]["risk_level"], extreme_result["weather_assessment"]["risk_level"])


if __name__ == "__main__":
    unittest.main()
