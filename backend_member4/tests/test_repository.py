import sqlite3
import unittest
from contextlib import closing
from pathlib import Path

from backend_member4.engine.planner import Planner
from backend_member4.repository import PersistenceError, RecommendationRepository


class TestRecommendationRepository(unittest.TestCase):
    """推荐结果 SQLite UPSERT 测试。"""

    def setUp(self):
        tests_directory = Path(__file__).resolve().parent
        self.db_path = tests_directory / ".repository_test.db"
        self.db_path.unlink(missing_ok=True)
        root = Path(__file__).resolve().parents[2]
        schema = (root / "database" / "01_schema.sql").read_text(encoding="utf-8-sig")
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                connection.executescript(schema)
                connection.execute(
                    "INSERT INTO user_account (user_id, username, password_hash, nickname) VALUES (1, 'member4', 'hash', '成员4')"
                )
                connection.execute(
                    """INSERT INTO user_profile (
                        user_id, age, gender, height_cm, weight_kg, goal,
                        activity_level, avg_sleep_hours, water_target_ml, profile_tag
                    ) VALUES (1, 24, 'female', 165, 55, 'maintain', 'medium', 7.5, 2200, '测试用户')"""
                )
        self.repository = RecommendationRepository(self.db_path)
        self.profile = {
            "user_id": 1,
            "age": 24,
            "gender": "female",
            "height_cm": 165,
            "weight_kg": 55,
            "goal": "maintain",
            "activity_level": "medium",
            "avg_sleep_hours": 7.5,
            "water_target_ml": 2200,
        }
        self.metrics = {
            "water_ml": 1500,
            "sport_duration_min": 30,
            "food_health_score": 80,
            "sleep_hours": 8,
            "sleep_quality_score": 85,
            "has_sleep_record": True,
        }
        self.weather = {
            "city": "上海",
            "temperature_c": 36,
            "humidity_pct": 75,
            "air_quality_index": 80,
            "uv_index": 7,
        }
        self.result = Planner().compose_plan(self.profile, self.metrics, self.weather, "2026-07-17")

    def tearDown(self):
        for suffix in ("", "-wal", "-shm", "-journal"):
            Path(f"{self.db_path}{suffix}").unlink(missing_ok=True)

    def test_plan_upsert_preserves_plan_identifier(self):
        """重复保存同日计划应更新原行而不是替换主键。"""
        first_id = self.repository.upsert_plan(1, "2026-07-17", self.result)
        changed = dict(self.result)
        changed["plan"] = dict(self.result["plan"], evening_advice="更新后的晚间建议")
        second_id = self.repository.upsert_plan(1, "2026-07-17", changed, health_target_score=85)
        self.assertEqual(first_id, second_id, "UPSERT 必须保留 plan_id")
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute(
                "SELECT evening_advice, health_target_score FROM daily_plan WHERE plan_id = ?",
                (first_id,),
            ).fetchone()
        self.assertEqual(row, ("更新后的晚间建议", 85))

    def test_weather_upsert_preserves_weather_identifier(self):
        """同城市同日期天气更新应保留 weather_id。"""
        assessment = self.result["weather_assessment"]
        first_id = self.repository.upsert_weather(assessment)
        changed = dict(assessment, advice=["更新后的天气建议"])
        second_id = self.repository.upsert_weather(changed)
        self.assertEqual(first_id, second_id, "UPSERT 必须保留 weather_id")

    def test_database_write_failure_raises_persistence_error(self):
        """数据库无法打开时必须抛出持久化异常。"""
        invalid_path = self.db_path.parent / ".missing_directory" / "database.db"
        repository = RecommendationRepository(invalid_path)
        with self.assertRaisesRegex(PersistenceError, "保存每日计划失败"):
            repository.upsert_plan(1, "2026-07-17", self.result)


if __name__ == "__main__":
    unittest.main()
