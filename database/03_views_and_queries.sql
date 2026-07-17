-- 伏日智护（FuCare）SQLite 联调视图与常用查询
-- 使用前请先执行 01_schema.sql 和 02_seed.sql

DROP VIEW IF EXISTS v_dashboard_daily;
DROP VIEW IF EXISTS v_daily_sleep_summary;
DROP VIEW IF EXISTS v_daily_sport_summary;
DROP VIEW IF EXISTS v_daily_water_summary;
DROP VIEW IF EXISTS v_daily_food_summary;

CREATE VIEW v_daily_food_summary AS
SELECT
  nutrition.user_id,
  nutrition.intake_date,
  nutrition.total_calorie_kcal,
  nutrition.total_protein_g,
  nutrition.total_food_water_ml,
  ROUND(
    (
      CASE
        WHEN nutrition.total_calorie_kcal BETWEEN 1200 AND 2200 THEN 100
        WHEN nutrition.total_calorie_kcal BETWEEN 900 AND 2600 THEN 80
        ELSE 60
      END
      +
      CASE
        WHEN nutrition.total_protein_g >= 60 THEN 100
        WHEN nutrition.total_protein_g >= 40 THEN 80
        ELSE 60
      END
      +
      CASE
        WHEN nutrition.total_food_water_ml >= 800 THEN 100
        WHEN nutrition.total_food_water_ml >= 500 THEN 80
        ELSE 60
      END
    ) / 3.0,
    2
  ) AS food_health_score
FROM (
  SELECT
    fr.user_id,
    fr.intake_date,
    ROUND(SUM(fl.calorie_kcal * fr.amount / 100.0), 2) AS total_calorie_kcal,
    ROUND(SUM(fl.protein_g * fr.amount / 100.0), 2) AS total_protein_g,
    ROUND(SUM(fl.water_ml * fr.amount / 100.0), 2) AS total_food_water_ml
  FROM food_record fr
  INNER JOIN food_library fl ON fl.food_id = fr.food_id
  GROUP BY fr.user_id, fr.intake_date
) AS nutrition;

CREATE VIEW v_daily_water_summary AS
SELECT
  user_id,
  date(intake_time) AS stat_date,
  SUM(amount_ml) AS total_water_ml,
  COUNT(*) AS drink_times
FROM water_record
GROUP BY user_id, date(intake_time);

CREATE VIEW v_daily_sport_summary AS
SELECT
  user_id,
  record_date,
  SUM(duration_min) AS total_duration_min,
  ROUND(SUM(calories_burned), 2) AS total_calories_burned,
  COUNT(*) AS sport_times
FROM sport_record
GROUP BY user_id, record_date;

CREATE VIEW v_daily_sleep_summary AS
SELECT
  user_id,
  record_date,
  ROUND(AVG((julianday(wake_time) - julianday(sleep_time)) * 24.0), 2) AS sleep_hours,
  ROUND(AVG(quality_score), 2) AS sleep_quality_score
FROM sleep_record
GROUP BY user_id, record_date;

CREATE VIEW v_dashboard_daily AS
SELECT
  dates.user_id,
  dates.stat_date,
  COALESCE(w.total_water_ml, 0) AS water_ml,
  COALESCE(s.total_duration_min, 0) AS sport_duration_min,
  COALESCE(s.total_calories_burned, 0) AS sport_calories_burned,
  COALESCE(f.total_calorie_kcal, 0) AS food_calorie_kcal,
  COALESCE(f.total_protein_g, 0) AS food_protein_g,
  COALESCE(f.food_health_score, 0) AS food_health_score,
  COALESCE(sl.sleep_hours, 0) AS sleep_hours,
  COALESCE(sl.sleep_quality_score, 0) AS sleep_quality_score,
  ROUND(
    MIN(COALESCE(w.total_water_ml, 0) * 1.0 / NULLIF(up.water_target_ml, 0), 1.0) * 30
    + MIN(COALESCE(s.total_duration_min, 0) * 1.0 / 30.0, 1.0) * 25
    + COALESCE(f.food_health_score, 0) / 100.0 * 25
    + COALESCE(sl.sleep_quality_score, 0) / 100.0 * 20,
    2
  ) AS health_score
FROM (
  SELECT user_id, intake_date AS stat_date FROM food_record
  UNION
  SELECT user_id, date(intake_time) AS stat_date FROM water_record
  UNION
  SELECT user_id, record_date AS stat_date FROM sport_record
  UNION
  SELECT user_id, record_date AS stat_date FROM sleep_record
  UNION
  SELECT user_id, plan_date AS stat_date FROM daily_plan
) AS dates
INNER JOIN user_profile up ON up.user_id = dates.user_id
LEFT JOIN v_daily_water_summary w
  ON w.user_id = dates.user_id AND w.stat_date = dates.stat_date
LEFT JOIN v_daily_sport_summary s
  ON s.user_id = dates.user_id AND s.record_date = dates.stat_date
LEFT JOIN v_daily_food_summary f
  ON f.user_id = dates.user_id AND f.intake_date = dates.stat_date
LEFT JOIN v_daily_sleep_summary sl
  ON sl.user_id = dates.user_id AND sl.record_date = dates.stat_date;

-- 1. 首页 Dashboard：查询指定用户某天的健康总览
WITH params AS (
  SELECT 1 AS target_user_id, '2026-07-17' AS target_date, '上海' AS target_city
)
SELECT
  ua.nickname,
  d.stat_date,
  d.health_score,
  d.water_ml,
  up.water_target_ml,
  d.sport_duration_min,
  d.food_calorie_kcal,
  d.food_protein_g,
  d.sleep_hours,
  d.sleep_quality_score,
  wd.temperature_c,
  wd.humidity_pct,
  wd.heat_risk,
  wd.advice,
  dp.breakfast_advice,
  dp.midday_advice,
  dp.exercise_advice,
  dp.evening_advice
FROM v_dashboard_daily d
INNER JOIN user_account ua ON ua.user_id = d.user_id
INNER JOIN user_profile up ON up.user_id = d.user_id
LEFT JOIN params p ON 1 = 1
LEFT JOIN weather_daily wd
  ON wd.weather_date = d.stat_date AND wd.city = p.target_city
LEFT JOIN daily_plan dp
  ON dp.user_id = d.user_id AND dp.plan_date = d.stat_date
WHERE d.user_id = p.target_user_id
  AND d.stat_date = p.target_date;

-- 2. 饮食模块：查看某用户每日营养摄入汇总
WITH params AS (
  SELECT 1 AS target_user_id
)
SELECT
  user_id,
  intake_date,
  total_calorie_kcal,
  total_protein_g,
  total_food_water_ml,
  food_health_score
FROM v_daily_food_summary
WHERE user_id = (SELECT target_user_id FROM params)
ORDER BY intake_date DESC;

-- 3. 运动模块：查看一周运动趋势
WITH params AS (
  SELECT 1 AS target_user_id, '2026-07-17' AS target_date
)
SELECT
  record_date,
  total_duration_min,
  total_calories_burned,
  sport_times
FROM v_daily_sport_summary
WHERE user_id = (SELECT target_user_id FROM params)
  AND record_date BETWEEN date((SELECT target_date FROM params), '-6 day') AND (SELECT target_date FROM params)
ORDER BY record_date;

-- 4. 睡眠模块：查看近 7 天睡眠时长与评分
WITH params AS (
  SELECT 1 AS target_user_id, '2026-07-17' AS target_date
)
SELECT
  record_date,
  sleep_hours,
  sleep_quality_score
FROM v_daily_sleep_summary
WHERE user_id = (SELECT target_user_id FROM params)
  AND record_date BETWEEN date((SELECT target_date FROM params), '-6 day') AND (SELECT target_date FROM params)
ORDER BY record_date;

-- 5. 用户画像模块：展示账号信息 + 健康画像
WITH params AS (
  SELECT 1 AS target_user_id
)
SELECT
  ua.user_id,
  ua.username,
  ua.nickname,
  up.age,
  up.gender,
  up.height_cm,
  up.weight_kg,
  up.bmi,
  up.goal,
  up.activity_level,
  up.avg_sleep_hours,
  up.profile_tag
FROM user_account ua
INNER JOIN user_profile up ON up.user_id = ua.user_id
WHERE ua.user_id = (SELECT target_user_id FROM params);

-- 6. 社区模块：展示最新动态
SELECT
  cp.post_id,
  ua.nickname,
  cp.content,
  cp.likes_count,
  cp.posted_at
FROM community_post cp
INNER JOIN user_account ua ON ua.user_id = cp.user_id
WHERE cp.visibility = 'public' AND cp.status = 1
ORDER BY cp.posted_at DESC
LIMIT 10;
