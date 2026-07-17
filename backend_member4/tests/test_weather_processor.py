import math
import unittest

from backend_member4.engine.weather_processor import WeatherProcessor, WeatherValidationError


class TestWeatherProcessor(unittest.TestCase):
    """天气标准化、三伏识别和风险分级测试。"""

    def setUp(self):
        self.processor = WeatherProcessor()
        self.weather = {
            "city": "上海",
            "temperature_c": 36,
            "humidity_pct": 75,
            "air_quality_index": 80,
            "uv_index": 7,
        }

    def test_date_in_first_sanfu_period_is_detected(self):
        """2026-07-17 应识别为初伏。"""
        result = self.processor.process(self.weather, "2026-07-17")
        self.assertTrue(result["is_sanfu"], "2026-07-17 应处于三伏")
        self.assertEqual(result["sanfu_stage"], "初伏")

    def test_date_outside_sanfu_period_is_not_detected(self):
        """三伏日期外不得触发三伏规则。"""
        result = self.processor.process(self.weather, "2026-06-17")
        self.assertFalse(result["is_sanfu"])
        self.assertIsNone(result["sanfu_stage"])

    def test_unsupported_year_is_reported_as_unknown(self):
        """未配置年份应返回未知状态而不是假装已判断。"""
        result = self.processor.process(self.weather, "2027-07-17")
        self.assertFalse(result["sanfu_known"])

    def test_extreme_heat_and_humidity_produce_extreme_risk(self):
        """38℃ 且湿度 80% 应判定为极端风险。"""
        weather = dict(self.weather, temperature_c=38, humidity_pct=80)
        result = self.processor.process(weather, "2026-07-17")
        self.assertEqual(result["risk_level"], "extreme")
        self.assertIn("extreme_heat", result["risk_factors"])

    def test_high_uv_produces_high_risk(self):
        """紫外线指数 8 以上应判定为高风险。"""
        weather = dict(self.weather, temperature_c=28, humidity_pct=50, uv_index=8)
        result = self.processor.process(weather, "2026-07-17")
        self.assertEqual(result["risk_level"], "high")
        self.assertIn("very_high_uv", result["risk_factors"])

    def test_invalid_weather_value_is_rejected(self):
        """湿度越界和非有限温度必须被拒绝。"""
        invalid_values = [
            dict(self.weather, humidity_pct=101),
            dict(self.weather, temperature_c=math.nan),
        ]
        for weather in invalid_values:
            with self.subTest(weather=weather):
                with self.assertRaises(WeatherValidationError):
                    self.processor.process(weather, "2026-07-17")


if __name__ == "__main__":
    unittest.main()
