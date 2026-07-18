import unittest

from backend_member4.engine.rule_engine import (
    RuleEngine,
    RuleValidationError,
    _eval_safe_expr,
    evaluate_condition,
)


class TestRuleEngine(unittest.TestCase):
    """规则解析、校验和执行测试。"""

    def test_safe_expression_addition_is_evaluated(self):
        """安全表达式应支持字段加法。"""
        context = {"user_profile": {"water_target_ml": 2000}}
        self.assertEqual(_eval_safe_expr("user_profile.water_target_ml + 300", context), 2300)

    def test_safe_expression_multiplication_is_evaluated(self):
        """安全表达式应支持字段乘法。"""
        context = {"user_profile": {"water_target_ml": 2000}}
        self.assertEqual(_eval_safe_expr("user_profile.water_target_ml * 0.5", context), 1000)

    def test_malicious_expression_is_not_executed(self):
        """不符合白名单格式的表达式不得执行。"""
        context = {"user_profile": {"water_target_ml": 2000}}
        expression = "__import__('os').system('echo unsafe')"
        self.assertIsNone(_eval_safe_expr(expression, context), "恶意表达式必须返回 None")

    def test_nested_condition_is_evaluated(self):
        """and、or 和字段比较应能组合使用。"""
        condition = {
            "and": [
                {"is_sanfu": True},
                {"or": [{"weather.temperature_c": {">=": 35}}, {"weather.uv_index": {">=": 8}}]},
            ]
        }
        context = {"is_sanfu": True, "weather": {"temperature_c": 36, "uv_index": 3}}
        self.assertTrue(evaluate_condition(condition, context))

    def test_duplicate_rule_identifier_is_rejected(self):
        """重复规则 ID 应在加载时失败。"""
        rules = [
            {"id": "duplicate", "when": True, "then": {"actions": []}},
            {"id": "duplicate", "when": True, "then": {"actions": []}},
        ]
        with self.assertRaisesRegex(RuleValidationError, "重复"):
            RuleEngine(rules)

    def test_unsupported_operator_is_rejected(self):
        """未支持的比较操作符应在加载时失败。"""
        rules = [{"id": "bad", "when": {"value": {"contains": 1}}, "then": {"actions": []}}]
        with self.assertRaisesRegex(RuleValidationError, "不支持的操作符"):
            RuleEngine(rules)

    def test_veto_is_not_duplicated(self):
        """规则同时声明 veto 和 veto 动作时只能输出一次。"""
        rules = [{
            "id": "heat",
            "priority": 10,
            "when": True,
            "then": {"actions": [{"type": "veto", "reason": "暂停活动"}], "veto": True},
        }]
        actions = RuleEngine(rules).run({})
        vetoes = [item for item in actions if item["action"]["type"] == "veto"]
        self.assertEqual(len(vetoes), 1, "同一规则不得产生重复 veto")

    def test_rules_continue_after_veto(self):
        """veto 不应阻止后续补水或防晒建议。"""
        rules = [
            {"id": "veto", "priority": 100, "when": True, "then": {"actions": [{"type": "veto", "reason": "暂停活动"}]}},
            {"id": "advice", "priority": 10, "when": True, "then": {"actions": [{"type": "advice", "slot": "midday", "text": "注意补水"}]}},
        ]
        actions = RuleEngine(rules).run({})
        self.assertEqual({item["rule_id"] for item in actions}, {"veto", "advice"})


if __name__ == "__main__":
    unittest.main()
