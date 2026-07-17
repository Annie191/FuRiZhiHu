import math
import unittest

from backend_member4.engine.health_scorer import HealthScorer, ScoreValidationError


class TestHealthScorer(unittest.TestCase):
    """健康任务完成分测试。"""

    def setUp(self):
        """初始化数据库口径的标准聚合指标。"""
        self.scorer = HealthScorer()
        self.profile = {"water_target_ml": 2200}
        self.metrics = {
            "water_ml": 1100,
            "sport_duration_min": 15,
            "food_health_score": 80,
            "sleep_quality_score": 90,
        }

    def test_score_matches_database_weight_formula(self):
        """评分应严格采用饮水30%、运动25%、饮食25%、睡眠20%。"""
        result = self.scorer.compute(self.profile, self.metrics)
        self.assertAlmostEqual(result["health_score"], 65.5, places=2, msg="评分必须与 SQL 权重公式一致")

    def test_score_uses_unrounded_completion_ratios(self):
        """总分应像 SQL 一样在最终阶段舍入，而不是先舍入子比例。"""
        metrics = {
            "water_ml": 1,
            "sport_duration_min": 1,
            "food_health_score": 60,
            "sleep_quality_score": 80,
        }
        expected = round(min(1 / 2200, 1) * 30 + min(1 / 30, 1) * 25 + 60 / 100 * 25 + 80 / 100 * 20, 2)
        result = self.scorer.compute(self.profile, metrics)
        self.assertEqual(result["health_score"], expected, "评分舍入顺序必须与 SQL 一致")

    def test_score_is_between_0_and_100(self):
        """总分应在 0 到 100 之间。"""
        result = self.scorer.compute(self.profile, self.metrics)
        self.assertGreaterEqual(result["health_score"], 0, "总分不能小于 0")
        self.assertLessEqual(result["health_score"], 100, "总分不能大于 100")

    def test_sub_scores_are_between_0_and_100(self):
        """所有子评分应在 0 到 100 之间。"""
        result = self.scorer.compute(self.profile, self.metrics)
        for dimension, score in result["sub_scores"].items():
            self.assertGreaterEqual(score, 0, f"{dimension} 子评分不能小于 0")
            self.assertLessEqual(score, 100, f"{dimension} 子评分不能大于 100")

    def test_completed_targets_produce_full_score(self):
        """所有指标达标时应得到 100 分。"""
        metrics = {
            "water_ml": 3000,
            "sport_duration_min": 60,
            "food_health_score": 100,
            "sleep_quality_score": 100,
        }
        self.assertEqual(self.scorer.compute(self.profile, metrics)["health_score"], 100)

    def test_weather_does_not_change_health_score(self):
        """相同行为数据不应因天气变化而改变健康分。"""
        normal = self.scorer.compute(self.profile, self.metrics, {"temperature_c": 25})
        extreme = self.scorer.compute(self.profile, self.metrics, {"temperature_c": 41})
        self.assertEqual(normal["health_score"], extreme["health_score"], "天气风险必须与健康分分离")
        self.assertEqual(extreme["env_penalty"], 0)

    def test_negative_metric_is_rejected(self):
        """负数指标必须被拒绝而不是产生负子分。"""
        metrics = dict(self.metrics, sport_duration_min=-1)
        with self.assertRaisesRegex(ScoreValidationError, "不能小于 0"):
            self.scorer.compute(self.profile, metrics)

    def test_out_of_range_score_metric_is_rejected(self):
        """超过 100 的睡眠质量必须被拒绝。"""
        metrics = dict(self.metrics, sleep_quality_score=101)
        with self.assertRaisesRegex(ScoreValidationError, "0 到 100"):
            self.scorer.compute(self.profile, metrics)

    def test_non_finite_metric_is_rejected(self):
        """NaN 和 Infinity 不得进入评分。"""
        for invalid in (math.nan, math.inf, -math.inf):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ScoreValidationError, "有限数字"):
                    self.scorer.compute(self.profile, dict(self.metrics, water_ml=invalid))

    def test_missing_required_metric_is_rejected(self):
        """缺少必要聚合指标时应返回明确校验错误。"""
        metrics = dict(self.metrics)
        del metrics["food_health_score"]
        with self.assertRaisesRegex(ScoreValidationError, "有限数字"):
            self.scorer.compute(self.profile, metrics)

    def test_invalid_weight_configuration_is_rejected(self):
        """权重总和不为 1 时不得启动评分器。"""
        config = {
            "algorithm_version": "test",
            "weights": {"water": 1, "sport": 1, "food": 1, "sleep": 1},
            "sport_target_min": 30,
        }
        with self.assertRaisesRegex(ScoreValidationError, "总和等于 1"):
            HealthScorer(config)


if __name__ == "__main__":
    unittest.main()
