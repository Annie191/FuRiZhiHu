-- 伏日智护（FuCare）SQLite 测试数据脚本
-- 使用前请先执行 01_schema.sql

PRAGMA foreign_keys = OFF;

DELETE FROM community_post;
DELETE FROM sleep_record;
DELETE FROM sport_record;
DELETE FROM water_record;
DELETE FROM food_record;
DELETE FROM food_library;
DELETE FROM daily_plan;
DELETE FROM weather_daily;
DELETE FROM user_profile;
DELETE FROM user_account;

DELETE FROM sqlite_sequence
WHERE name IN (
  'community_post',
  'sleep_record',
  'sport_record',
  'water_record',
  'food_record',
  'food_library',
  'daily_plan',
  'weather_daily',
  'user_account'
);

PRAGMA foreign_keys = ON;

INSERT INTO user_account (user_id, username, password_hash, nickname, phone, email)
VALUES
  (1, 'zhangsan', '$2b$10$demo.hash.for.zhangsan', '张同学', '13800000001', 'zhangsan@furicare.com'),
  (2, 'lisi', '$2b$10$demo.hash.for.lisi', '李同学', '13800000002', 'lisi@furicare.com'),
  (3, 'wangwu', '$2b$10$demo.hash.for.wangwu', '王同学', '13800000003', 'wangwu@furicare.com');

INSERT INTO user_profile (user_id, age, gender, height_cm, weight_kg, goal, activity_level, avg_sleep_hours, water_target_ml, profile_tag)
VALUES
  (1, 22, 'male', 175.00, 70.00, 'lose_fat', 'low', 6.5, 2200, '夏季减脂型用户'),
  (2, 21, 'female', 163.00, 54.00, 'maintain', 'medium', 7.2, 2000, '规律养生型用户'),
  (3, 23, 'male', 180.00, 76.00, 'gain_muscle', 'high', 7.8, 2600, '增肌训练型用户');

INSERT INTO weather_daily (city, weather_date, temperature_c, humidity_pct, uv_index, air_quality_index, heat_risk, advice)
VALUES
  ('上海', '2026-07-17', 36.0, 75, 8, 78, 'high', '10:00-16:00 尽量避免长时间户外运动，及时补水。'),
  ('上海', '2026-07-18', 35.0, 70, 7, 74, 'high', '外出注意防晒，建议晚间进行轻度运动。'),
  ('杭州', '2026-07-17', 35.5, 72, 8, 70, 'high', '高温闷热，建议减少户外暴晒时间。');

INSERT INTO daily_plan (user_id, plan_date, breakfast_advice, midday_advice, exercise_advice, evening_advice, health_target_score, status)
VALUES
  (1, '2026-07-17', '鸡蛋 + 牛奶 + 玉米，少油少盐', '上午分两次补水共 500ml', '18:00 后快走 30 分钟', '23:30 前入睡，睡前减少刷手机', 85, 'pending'),
  (1, '2026-07-18', '燕麦 + 水煮蛋 + 苹果', '午休 20 分钟并补水 400ml', '晚间拉伸 15 分钟 + 慢走 20 分钟', '避免夜宵，23:00 前休息', 86, 'pending'),
  (2, '2026-07-17', '牛奶 + 全麦面包 + 香蕉', '午后补水 400ml，避免高糖饮料', '傍晚瑜伽 20 分钟', '保持 7 小时以上睡眠', 88, 'completed');

INSERT INTO food_library (food_id, name, calorie_kcal, protein_g, water_ml, category, season, unit_basis, note)
VALUES
  (1, '西瓜', 30.00, 0.60, 91.50, 'fruit', 'summer', 'per_100g', '夏季补水水果'),
  (2, '鸡蛋', 144.00, 13.30, 76.70, 'protein', 'all', 'per_100g', '优质蛋白来源'),
  (3, '牛奶', 54.00, 3.30, 88.00, 'beverage', 'all', 'per_100ml', '补钙补蛋白'),
  (4, '玉米', 112.00, 4.00, 71.00, 'grain', 'summer', 'per_100g', '饱腹感较强'),
  (5, '鸡胸肉', 133.00, 24.00, 72.00, 'protein', 'all', 'per_100g', '低脂高蛋白'),
  (6, '黄瓜', 16.00, 0.80, 95.80, 'vegetable', 'summer', 'per_100g', '清爽低热量'),
  (7, '燕麦片', 367.00, 15.00, 10.00, 'grain', 'all', 'per_100g', '适合早餐'),
  (8, '酸奶', 72.00, 2.50, 85.00, 'beverage', 'all', 'per_100ml', '适合作为加餐');

INSERT INTO food_record (user_id, food_id, meal_type, amount, amount_unit, intake_date, note)
VALUES
  (1, 2, 'breakfast', 100.00, 'g', '2026-07-17', '水煮蛋 2 个'),
  (1, 3, 'breakfast', 250.00, 'ml', '2026-07-17', '纯牛奶 1 杯'),
  (1, 4, 'breakfast', 150.00, 'g', '2026-07-17', '早餐玉米 1 根'),
  (1, 5, 'lunch', 180.00, 'g', '2026-07-17', '清煮鸡胸肉'),
  (1, 6, 'lunch', 200.00, 'g', '2026-07-17', '凉拌黄瓜'),
  (1, 1, 'snack', 300.00, 'g', '2026-07-17', '下午加餐'),
  (2, 3, 'breakfast', 250.00, 'ml', '2026-07-17', '早餐牛奶'),
  (2, 8, 'snack', 200.00, 'ml', '2026-07-17', '午后酸奶');

INSERT INTO water_record (user_id, amount_ml, source, intake_time, note)
VALUES
  (1, 300, 'water', '2026-07-17 08:00:00', '晨起补水'),
  (1, 400, 'water', '2026-07-17 10:30:00', '上午补水'),
  (1, 500, 'tea', '2026-07-17 14:00:00', '淡茶'),
  (1, 350, 'water', '2026-07-17 18:30:00', '运动后补水'),
  (2, 300, 'water', '2026-07-17 09:00:00', '晨间补水'),
  (2, 400, 'soup', '2026-07-17 12:30:00', '午餐汤类');

INSERT INTO sport_record (user_id, sport_type, intensity, duration_min, calories_burned, record_date, start_time, note)
VALUES
  (1, '快走', 'medium', 35, 210.00, '2026-07-17', '18:10:00', '傍晚室外快走'),
  (2, '瑜伽', 'low', 20, 85.00, '2026-07-17', '19:00:00', '居家拉伸'),
  (3, '力量训练', 'high', 50, 360.00, '2026-07-17', '20:00:00', '上肢训练');

INSERT INTO sleep_record (user_id, sleep_time, wake_time, quality_score, record_date, note)
VALUES
  (1, '2026-07-16 23:55:00', '2026-07-17 06:40:00', 78, '2026-07-17', '睡前刷手机较久'),
  (2, '2026-07-16 23:10:00', '2026-07-17 06:50:00', 85, '2026-07-17', '睡眠较稳定'),
  (3, '2026-07-16 22:50:00', '2026-07-17 07:00:00', 90, '2026-07-17', '恢复状态较好');

INSERT INTO community_post (user_id, content, posted_at, likes_count, visibility)
VALUES
  (1, '今天完成了 35 分钟快走，出汗很多，记得补水。', '2026-07-17 20:10:00', 6, 'public'),
  (2, '午后做了 20 分钟瑜伽，感觉肩颈舒服很多。', '2026-07-17 20:30:00', 4, 'public');
