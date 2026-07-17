from pathlib import Path
import sqlite3
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_PATHS = [
    SCRIPT_DIR / "01_schema.sql",
    SCRIPT_DIR / "02_seed.sql",
    SCRIPT_DIR / "03_views_and_queries.sql",
]


class SQLiteDatabaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        for script_path in SCRIPT_PATHS:
            self.conn.executescript(script_path.read_text(encoding="utf-8"))
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def tearDown(self) -> None:
        self.conn.close()


class SeedCoverageTests(SQLiteDatabaseTestCase):
    def test_full_week_seed_data_covers_two_users_and_all_modules(self) -> None:
        row = self.conn.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM user_account) AS user_count,
              (SELECT COUNT(*) FROM weather_daily) AS weather_count,
              (SELECT COUNT(*) FROM daily_plan) AS plan_count,
              (SELECT COUNT(*) FROM food_record) AS food_count,
              (SELECT COUNT(*) FROM water_record) AS water_count,
              (SELECT COUNT(*) FROM sport_record) AS sport_count,
              (SELECT COUNT(*) FROM sleep_record) AS sleep_count,
              (SELECT COUNT(*) FROM community_post) AS post_count,
              (SELECT COUNT(DISTINCT plan_date) FROM daily_plan) AS plan_day_count
            """
        ).fetchone()

        self.assertEqual(row["user_count"], 2)
        self.assertEqual(row["weather_count"], 14)
        self.assertEqual(row["plan_count"], 14)
        self.assertEqual(row["food_count"], 84)
        self.assertEqual(row["water_count"], 56)
        self.assertEqual(row["sport_count"], 14)
        self.assertEqual(row["sleep_count"], 14)
        self.assertEqual(row["post_count"], 8)
        self.assertEqual(row["plan_day_count"], 7)


class Member1FrontendTests(SQLiteDatabaseTestCase):
    def test_dashboard_card_data_is_ready_for_homepage_rendering(self) -> None:
        row = self.conn.execute(
            """
            SELECT
              ua.nickname,
              d.stat_date,
              d.health_score,
              d.water_ml,
              up.water_target_ml,
              d.sport_duration_min,
              d.food_calorie_kcal,
              d.sleep_quality_score,
              wd.heat_risk,
              dp.exercise_advice
            FROM v_dashboard_daily d
            JOIN user_account ua ON ua.user_id = d.user_id
            JOIN user_profile up ON up.user_id = d.user_id
            LEFT JOIN weather_daily wd
              ON wd.city = '上海' AND wd.weather_date = d.stat_date
            LEFT JOIN daily_plan dp
              ON dp.user_id = d.user_id AND dp.plan_date = d.stat_date
            WHERE d.user_id = 1 AND d.stat_date = '2026-07-17'
            """
        ).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row["nickname"], "张同学")
        self.assertAlmostEqual(row["health_score"], 83.4, places=1)
        self.assertEqual(row["water_ml"], 1550)
        self.assertEqual(row["water_target_ml"], 2200)
        self.assertEqual(row["sport_duration_min"], 35)
        self.assertEqual(row["heat_risk"], "high")
        self.assertIn("18:00 后快走 30 分钟", row["exercise_advice"])

    def test_frontend_can_render_trend_chart_and_community_feed(self) -> None:
        sport_row = self.conn.execute(
            """
            SELECT record_date, total_duration_min, total_calories_burned, sport_times
            FROM v_daily_sport_summary
            WHERE user_id = 1
            ORDER BY record_date DESC
            LIMIT 1
            """
        ).fetchone()
        post_rows = self.conn.execute(
            """
            SELECT ua.nickname, cp.content, cp.likes_count
            FROM community_post cp
            JOIN user_account ua ON ua.user_id = cp.user_id
            WHERE cp.visibility = 'public' AND cp.status = 1
            ORDER BY cp.posted_at DESC
            """
        ).fetchall()

        self.assertEqual(sport_row["record_date"], "2026-07-17")
        self.assertEqual(sport_row["total_duration_min"], 35)
        self.assertEqual(sport_row["sport_times"], 1)
        self.assertGreaterEqual(len(post_rows), 2)
        self.assertEqual(post_rows[0]["nickname"], "李同学")
        self.assertIn("瑜伽", post_rows[0]["content"])


class Member3ApiTests(SQLiteDatabaseTestCase):
    def test_api_layer_can_register_user_and_write_full_day_records(self) -> None:
        self.conn.execute(
            """
            INSERT INTO user_account (username, password_hash, nickname, phone, email)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("zhaoliu", "demo_hash", "赵同学", "13800000004", "zhaoliu@furicare.com"),
        )
        user_id = self.conn.execute(
            "SELECT user_id FROM user_account WHERE username = ?",
            ("zhaoliu",),
        ).fetchone()["user_id"]

        self.conn.execute(
            """
            INSERT INTO user_profile (
              user_id, age, gender, height_cm, weight_kg, goal,
              activity_level, avg_sleep_hours, water_target_ml, profile_tag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, 24, "female", 165.0, 55.0, "maintain", "medium", 7.5, 2100, "稳定作息型用户"),
        )
        self.conn.execute(
            """
            INSERT INTO daily_plan (
              user_id, plan_date, breakfast_advice, midday_advice,
              exercise_advice, evening_advice, health_target_score, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, "2026-07-17", "燕麦牛奶", "补水 400ml", "慢跑 20 分钟", "23:00 前休息", 90, "pending"),
        )
        self.conn.execute(
            """
            INSERT INTO food_record (user_id, food_id, meal_type, amount, amount_unit, intake_date, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, 7, "breakfast", 80.0, "g", "2026-07-17", "早餐燕麦"),
        )
        self.conn.execute(
            """
            INSERT INTO water_record (user_id, amount_ml, source, intake_time, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, 500, "water", "2026-07-17 09:00:00", "晨间补水"),
        )
        self.conn.execute(
            """
            INSERT INTO sport_record (user_id, sport_type, intensity, duration_min, calories_burned, record_date, start_time, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, "慢跑", "medium", 20, 160.0, "2026-07-17", "18:30:00", "晚间慢跑"),
        )
        self.conn.execute(
            """
            INSERT INTO sleep_record (user_id, sleep_time, wake_time, quality_score, record_date, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, "2026-07-16 23:20:00", "2026-07-17 07:00:00", 88, "2026-07-17", "睡眠稳定"),
        )
        self.conn.commit()

        row = self.conn.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM user_profile WHERE user_id = ?) AS profile_count,
              (SELECT COUNT(*) FROM daily_plan WHERE user_id = ?) AS plan_count,
              (SELECT COUNT(*) FROM food_record WHERE user_id = ?) AS food_count,
              (SELECT COUNT(*) FROM water_record WHERE user_id = ?) AS water_count,
              (SELECT COUNT(*) FROM sport_record WHERE user_id = ?) AS sport_count,
              (SELECT COUNT(*) FROM sleep_record WHERE user_id = ?) AS sleep_count
            """,
            (user_id, user_id, user_id, user_id, user_id, user_id),
        ).fetchone()

        self.assertEqual(row["profile_count"], 1)
        self.assertEqual(row["plan_count"], 1)
        self.assertEqual(row["food_count"], 1)
        self.assertEqual(row["water_count"], 1)
        self.assertEqual(row["sport_count"], 1)
        self.assertEqual(row["sleep_count"], 1)

    def test_api_layer_is_protected_by_unique_and_foreign_key_constraints(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO user_account (username, password_hash, nickname, phone, email)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("zhangsan", "another_hash", "重复账号", "13800009999", "dup@furicare.com"),
            )

        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO food_record (user_id, food_id, meal_type, amount, amount_unit, intake_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (999, 1, "breakfast", 100.0, "g", "2026-07-17"),
            )


class Member4RecommendationTests(SQLiteDatabaseTestCase):
    def test_health_score_view_matches_rule_weight_formula(self) -> None:
        row = self.conn.execute(
            """
            SELECT
              d.water_ml,
              up.water_target_ml,
              d.sport_duration_min,
              d.food_health_score,
              d.sleep_quality_score,
              d.health_score
            FROM v_dashboard_daily d
            JOIN user_profile up ON up.user_id = d.user_id
            WHERE d.user_id = 1 AND d.stat_date = '2026-07-17'
            """
        ).fetchone()

        manual_score = round(
            min(row["water_ml"] / row["water_target_ml"], 1.0) * 30
            + min(row["sport_duration_min"] / 30.0, 1.0) * 25
            + row["food_health_score"] / 100.0 * 25
            + row["sleep_quality_score"] / 100.0 * 20,
            2,
        )

        self.assertAlmostEqual(row["health_score"], manual_score, places=2)
        self.assertAlmostEqual(row["health_score"], 83.4, places=1)

    def test_recommendation_module_can_store_weather_and_plan_outputs(self) -> None:
        self.conn.execute(
            """
            INSERT INTO weather_daily (
              city, weather_date, temperature_c, humidity_pct, uv_index,
              air_quality_index, heat_risk, advice
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("南京", "2026-07-19", 37.5, 73, 9, 82, "extreme", "避免午后外出，增加室内补水频率。"),
        )
        self.conn.execute(
            """
            INSERT INTO daily_plan (
              user_id, plan_date, breakfast_advice, midday_advice,
              exercise_advice, evening_advice, health_target_score, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (2, "2026-07-19", "鸡蛋 + 燕麦", "补水 600ml", "改为室内拉伸", "22:50 前休息", 92, "pending"),
        )
        self.conn.commit()

        row = self.conn.execute(
            """
            SELECT wd.heat_risk, wd.advice, dp.exercise_advice, dp.health_target_score
            FROM weather_daily wd
            JOIN daily_plan dp ON dp.plan_date = wd.weather_date
            WHERE wd.city = '南京' AND dp.user_id = 2 AND dp.plan_date = '2026-07-19'
            """
        ).fetchone()

        self.assertEqual(row["heat_risk"], "extreme")
        self.assertIn("避免午后外出", row["advice"])
        self.assertIn("室内拉伸", row["exercise_advice"])
        self.assertEqual(row["health_target_score"], 92)

        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO daily_plan (
                  user_id, plan_date, breakfast_advice, midday_advice,
                  exercise_advice, evening_advice, health_target_score, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (2, "2026-07-19", "重复计划", "重复计划", "重复计划", "重复计划", 60, "pending"),
            )


class Member5ProfileAnalysisTests(SQLiteDatabaseTestCase):
    def test_generated_bmi_supports_profile_analysis(self) -> None:
        row = self.conn.execute(
            """
            SELECT nickname, bmi, profile_tag, goal, activity_level
            FROM user_account ua
            JOIN user_profile up ON up.user_id = ua.user_id
            WHERE ua.user_id = 1
            """
        ).fetchone()

        self.assertEqual(row["nickname"], "张同学")
        self.assertAlmostEqual(row["bmi"], 22.86, places=2)
        self.assertEqual(row["profile_tag"], "夏季减脂型用户")
        self.assertEqual(row["goal"], "lose_fat")
        self.assertEqual(row["activity_level"], "low")

    def test_profile_analysis_member_can_build_summary_report_from_database(self) -> None:
        row = self.conn.execute(
            """
            SELECT
              ua.nickname,
              up.profile_tag,
              up.bmi,
              (SELECT ROUND(AVG(quality_score), 2) FROM sleep_record WHERE user_id = ua.user_id) AS avg_sleep_quality,
              (SELECT ROUND(SUM(calories_burned), 2) FROM sport_record WHERE user_id = ua.user_id) AS total_burned,
              (SELECT ROUND(SUM(amount_ml), 2) FROM water_record WHERE user_id = ua.user_id AND date(intake_time) = '2026-07-17') AS daily_water,
              (SELECT COUNT(*) FROM community_post WHERE user_id = ua.user_id) AS post_count
            FROM user_account ua
            JOIN user_profile up ON up.user_id = ua.user_id
            WHERE ua.user_id = 1
            """
        ).fetchone()

        self.assertEqual(row["nickname"], "张同学")
        self.assertEqual(row["profile_tag"], "夏季减脂型用户")
        self.assertAlmostEqual(row["avg_sleep_quality"], 78.57, places=2)
        self.assertAlmostEqual(row["total_burned"], 1340.0, places=1)
        self.assertEqual(row["daily_water"], 1550)
        self.assertEqual(row["post_count"], 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
