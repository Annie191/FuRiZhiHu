"""可校验、可配置且不执行任意代码的轻量规则引擎。"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence


class RuleValidationError(ValueError):
    """规则结构或字段不符合约定。"""


class RuleEvaluationError(RuntimeError):
    """规则运行时无法完成比较。"""


def _get_path(context: Mapping[str, Any], path: str) -> Any:
    current: Any = context
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


_SAFE_EXPR_PATTERN = re.compile(
    r"^user_profile\.([a-zA-Z_][a-zA-Z0-9_]*)\s*([+\-*/])\s*([0-9]+(?:\.[0-9]+)?)$"
)


def _eval_safe_expr(expr: str, context: Mapping[str, Any]) -> float | None:
    """仅解析 user_profile.字段 与一个数字的四则运算。"""
    match = _SAFE_EXPR_PATTERN.match(expr.strip())
    if not match:
        return None
    field_name, operator, raw_number = match.groups()
    profile = context.get("user_profile", {})
    if not isinstance(profile, Mapping) or field_name not in profile:
        return None
    try:
        left = float(profile[field_name])
        right = float(raw_number)
    except (TypeError, ValueError):
        return None
    if operator == "+":
        return left + right
    if operator == "-":
        return left - right
    if operator == "*":
        return left * right
    if operator == "/" and right != 0:
        return left / right
    return None


def _eval_comparison(left: Any, comparison: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    for operator, expected in comparison.items():
        right = _eval_safe_expr(expected, context) if isinstance(expected, str) and "user_profile" in expected else expected
        try:
            if operator == "==" and left != right:
                return False
            if operator == "!=" and left == right:
                return False
            if operator == ">=" and (left is None or right is None or left < right):
                return False
            if operator == "<=" and (left is None or right is None or left > right):
                return False
            if operator == ">" and (left is None or right is None or left <= right):
                return False
            if operator == "<" and (left is None or right is None or left >= right):
                return False
        except TypeError as error:
            raise RuleEvaluationError(f"无法比较 {left!r} 与 {right!r}。") from error
    return True


def evaluate_condition(condition: Any, context: Mapping[str, Any]) -> bool:
    """递归计算 and/or/not/any/all 和字段比较条件。"""
    if condition is None:
        return True
    if isinstance(condition, bool):
        return condition
    if not isinstance(condition, Mapping):
        return False
    if "and" in condition:
        return all(evaluate_condition(item, context) for item in condition["and"])
    if "or" in condition:
        return any(evaluate_condition(item, context) for item in condition["or"])
    if "not" in condition:
        return not evaluate_condition(condition["not"], context)
    if "any" in condition:
        return any(evaluate_condition(item, context) for item in condition["any"])
    if "all" in condition:
        return all(evaluate_condition(item, context) for item in condition["all"])
    for path, rule in condition.items():
        left = _get_path(context, path)
        if isinstance(rule, Mapping):
            if not _eval_comparison(left, rule, context):
                return False
        elif left != rule:
            return False
    return True


class RuleEngine:
    """按优先级执行经过结构校验的建议与 veto 规则。"""

    _OPERATORS = {"==", "!=", ">=", "<=", ">", "<"}
    _ACTION_TYPES = {"advice", "veto"}
    _SLOTS = {"breakfast", "midday", "exercise", "evening"}

    def __init__(self, rules: Sequence[Mapping[str, Any]]):
        self.rules = self._validate_rules(rules)

    def run(self, context: Mapping[str, Any]) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        seen_actions: set[tuple[Any, ...]] = set()
        for rule in self.rules:
            if not evaluate_condition(rule.get("when"), context):
                continue
            configured = list(rule["then"].get("actions", []))
            has_veto = any(action.get("type") == "veto" for action in configured)
            if rule["then"].get("veto") and not has_veto:
                configured.append({"type": "veto", "reason": f"被规则 {rule['id']} 限制"})
            for action in configured:
                signature = (
                    action.get("type"),
                    action.get("slot"),
                    action.get("text"),
                    action.get("reason"),
                )
                if signature in seen_actions:
                    continue
                seen_actions.add(signature)
                actions.append({
                    "rule_id": rule["id"],
                    "priority": rule.get("priority", 0),
                    "action": dict(action),
                })
        return actions

    @classmethod
    def _validate_rules(cls, rules: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        if isinstance(rules, (str, bytes)) or not isinstance(rules, Sequence):
            raise RuleValidationError("规则配置必须是列表。")
        validated: list[dict[str, Any]] = []
        identifiers: set[str] = set()
        for raw_rule in rules:
            if not isinstance(raw_rule, Mapping):
                raise RuleValidationError("每条规则必须是对象。")
            identifier = raw_rule.get("id")
            if not isinstance(identifier, str) or not identifier.strip():
                raise RuleValidationError("规则 id 必须是非空字符串。")
            if identifier in identifiers:
                raise RuleValidationError(f"规则 id 重复：{identifier}")
            identifiers.add(identifier)
            priority = raw_rule.get("priority", 0)
            if isinstance(priority, bool) or not isinstance(priority, int):
                raise RuleValidationError(f"规则 {identifier} 的 priority 必须是整数。")
            then = raw_rule.get("then", {})
            if not isinstance(then, Mapping) or not isinstance(then.get("actions", []), list):
                raise RuleValidationError(f"规则 {identifier} 的 then.actions 必须是列表。")
            cls._validate_condition(raw_rule.get("when"), identifier)
            for action in then.get("actions", []):
                if not isinstance(action, Mapping) or action.get("type") not in cls._ACTION_TYPES:
                    raise RuleValidationError(f"规则 {identifier} 包含不支持的动作。")
                if action["type"] == "advice":
                    if action.get("slot") not in cls._SLOTS or not isinstance(action.get("text"), str) or not action["text"].strip():
                        raise RuleValidationError(f"规则 {identifier} 的 advice 动作无效。")
                if action["type"] == "veto" and (not isinstance(action.get("reason"), str) or not action["reason"].strip()):
                    raise RuleValidationError(f"规则 {identifier} 的 veto 原因无效。")
            if raw_rule.get("enabled", True):
                validated.append(dict(raw_rule))
        validated.sort(key=lambda item: item.get("priority", 0), reverse=True)
        return validated

    @classmethod
    def _validate_condition(cls, condition: Any, rule_id: str) -> None:
        if condition is None or isinstance(condition, bool):
            return
        if not isinstance(condition, Mapping):
            raise RuleValidationError(f"规则 {rule_id} 的 when 必须是对象或布尔值。")
        for key, value in condition.items():
            if key in {"and", "or", "any", "all"}:
                if not isinstance(value, list):
                    raise RuleValidationError(f"规则 {rule_id} 的 {key} 必须是列表。")
                for child in value:
                    cls._validate_condition(child, rule_id)
            elif key == "not":
                cls._validate_condition(value, rule_id)
            elif isinstance(value, Mapping):
                unsupported = set(value) - cls._OPERATORS
                if unsupported:
                    raise RuleValidationError(f"规则 {rule_id} 包含不支持的操作符：{sorted(unsupported)}")
