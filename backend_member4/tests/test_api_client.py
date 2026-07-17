import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from backend_member4.api_client import (
    AuthenticationError,
    Member3HealthApiClient,
    UpstreamProtocolError,
    UpstreamServiceError,
    UpstreamUnavailableError,
    UpstreamValidationError,
)


class StubHTTPError(HTTPError):
    """不持有文件句柄的 HTTPError 测试替身。"""

    def __init__(self, status):
        Exception.__init__(self, f"HTTP {status}")
        self.code = status


class FakeResponse:
    """支持 urlopen 上下文协议的测试响应。"""

    def __init__(self, payload):
        self.payload = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.payload


class TestMember3HealthApiClient(unittest.TestCase):
    """成员 3 HTTP 接口字段映射和错误处理测试。"""

    def setUp(self):
        self.token = "secret-access-token"
        self.client = Member3HealthApiClient("http://127.0.0.1:3000/api/v1", self.token)
        self.user_payload = {
            "data": {
                "user": {
                    "id": 7,
                    "profile": {
                        "age": 24,
                        "gender": "female",
                        "heightCm": 165,
                        "weightKg": 55,
                        "goal": "maintain",
                        "activityLevel": "medium",
                        "avgSleepHours": 7.5,
                        "waterTargetMl": 2200,
                        "profileTag": "规律作息型用户",
                    },
                }
            }
        }

    def _success_responses(self, sleep_rows=None):
        if sleep_rows is None:
            sleep_rows = [{"date": "2026-07-17", "sleepHours": 8, "sleepQualityScore": 80}]
        return [
            FakeResponse(self.user_payload),
            FakeResponse({"data": [{"date": "2026-07-17", "foodHealthScore": 75}]}),
            FakeResponse({"data": [{"date": "2026-07-17", "totalWaterMl": 1500}]}),
            FakeResponse({"data": [{"date": "2026-07-17", "totalDurationMin": 30}]}),
            FakeResponse({"data": sleep_rows}),
        ]

    @patch("backend_member4.api_client.urlopen")
    def test_member3_api_context_maps_daily_summaries(self, mocked_urlopen):
        """成员3五个接口应正确转换为成员4推荐上下文。"""
        mocked_urlopen.side_effect = self._success_responses()
        context = self.client.fetch_recommendation_context("2026-07-17")
        self.assertEqual(context.profile["user_id"], 7)
        self.assertEqual(context.profile["water_target_ml"], 2200)
        self.assertEqual(context.metrics["water_ml"], 1500)
        self.assertEqual(context.metrics["sport_duration_min"], 30)
        self.assertEqual(context.metrics["food_health_score"], 75)
        self.assertEqual(context.metrics["sleep_quality_score"], 80)
        self.assertTrue(context.metrics["has_sleep_record"])
        for call in mocked_urlopen.call_args_list:
            request = call.args[0]
            self.assertEqual(request.get_header("Authorization"), f"Bearer {self.token}")

    @patch("backend_member4.api_client.urlopen")
    def test_empty_sleep_summary_preserves_missing_record_state(self, mocked_urlopen):
        """睡眠汇总为空时应使用零分并保留无记录状态。"""
        mocked_urlopen.side_effect = self._success_responses(sleep_rows=[])
        context = self.client.fetch_recommendation_context("2026-07-17")
        self.assertEqual(context.metrics["sleep_hours"], 0)
        self.assertEqual(context.metrics["sleep_quality_score"], 0)
        self.assertFalse(context.metrics["has_sleep_record"])

    @patch("backend_member4.api_client.urlopen")
    def test_http_errors_are_mapped_to_specific_exceptions(self, mocked_urlopen):
        """401、400 和 500 应映射为不同异常。"""
        mappings = [
            (401, AuthenticationError),
            (400, UpstreamValidationError),
            (500, UpstreamServiceError),
        ]
        for status, expected in mappings:
            with self.subTest(status=status):
                mocked_urlopen.side_effect = StubHTTPError(status)
                with self.assertRaises(expected):
                    self.client.fetch_recommendation_context("2026-07-17")

    @patch("backend_member4.api_client.urlopen")
    def test_network_failure_is_mapped_to_unavailable_error(self, mocked_urlopen):
        """连接失败或超时应转换为上游不可用异常。"""
        mocked_urlopen.side_effect = URLError("connection refused")
        with self.assertRaises(UpstreamUnavailableError):
            self.client.fetch_recommendation_context("2026-07-17")

    @patch("backend_member4.api_client.urlopen")
    def test_invalid_json_is_rejected(self, mocked_urlopen):
        """非法 JSON 应作为协议错误处理。"""
        mocked_urlopen.return_value = FakeResponse(b"not-json")
        with self.assertRaisesRegex(UpstreamProtocolError, "无效 JSON"):
            self.client.fetch_recommendation_context("2026-07-17")

    @patch("backend_member4.api_client.urlopen")
    def test_access_token_is_not_exposed_in_error_message(self, mocked_urlopen):
        """任何上游异常都不得把 JWT 放进错误文本。"""
        mocked_urlopen.side_effect = StubHTTPError(401)
        with self.assertRaises(AuthenticationError) as raised:
            self.client.fetch_recommendation_context("2026-07-17")
        self.assertNotIn(self.token, str(raised.exception), "错误信息不得泄露 JWT")

    @patch("backend_member4.api_client.urlopen")
    def test_multiple_daily_summary_rows_are_rejected(self, mocked_urlopen):
        """指定日期汇总返回多行时应判定契约异常。"""
        duplicated = [
            {"date": "2026-07-17", "foodHealthScore": 70},
            {"date": "2026-07-17", "foodHealthScore": 80},
        ]
        mocked_urlopen.side_effect = [FakeResponse(self.user_payload), FakeResponse({"data": duplicated})]
        with self.assertRaisesRegex(UpstreamProtocolError, "零或一项"):
            self.client.fetch_recommendation_context("2026-07-17")


if __name__ == "__main__":
    unittest.main()
