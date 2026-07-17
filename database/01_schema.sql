-- 伏日智护（FuCare）SQLite 数据库初始化脚本
-- 适用版本：SQLite 3.31+

PRAGMA foreign_keys = OFF;

DROP VIEW IF EXISTS v_dashboard_daily;
DROP VIEW IF EXISTS v_daily_sleep_summary;
DROP VIEW IF EXISTS v_daily_sport_summary;
DROP VIEW IF EXISTS v_daily_water_summary;
DROP VIEW IF EXISTS v_daily_food_summary;

DROP TRIGGER IF EXISTS trg_user_account_updated_at;
DROP TRIGGER IF EXISTS trg_user_profile_updated_at;
DROP TRIGGER IF EXISTS trg_daily_plan_updated_at;
DROP TRIGGER IF EXISTS trg_food_library_updated_at;

DROP TABLE IF EXISTS community_post;
DROP TABLE IF EXISTS sleep_record;
DROP TABLE IF EXISTS sport_record;
DROP TABLE IF EXISTS water_record;
DROP TABLE IF EXISTS food_record;
DROP TABLE IF EXISTS food_library;
DROP TABLE IF EXISTS daily_plan;
DROP TABLE IF EXISTS weather_daily;
DROP TABLE IF EXISTS user_profile;
DROP TABLE IF EXISTS user_account;

PRAGMA foreign_keys = ON;

-- 用户账号表
CREATE TABLE user_account (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  nickname TEXT NOT NULL,
  phone TEXT UNIQUE,
  email TEXT UNIQUE,
  status INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 用户健康画像表
CREATE TABLE user_profile (
  user_id INTEGER PRIMARY KEY,
  age INTEGER NOT NULL CHECK (age BETWEEN 10 AND 100),
  gender TEXT NOT NULL CHECK (gender IN ('male', 'female', 'other')),
  height_cm REAL NOT NULL CHECK (height_cm BETWEEN 100 AND 250),
  weight_kg REAL NOT NULL CHECK (weight_kg BETWEEN 20 AND 300),
  goal TEXT NOT NULL CHECK (goal IN ('lose_fat', 'maintain', 'gain_muscle')),
  activity_level TEXT NOT NULL CHECK (activity_level IN ('low', 'medium', 'high')),
  avg_sleep_hours REAL NOT NULL CHECK (avg_sleep_hours BETWEEN 0 AND 24),
  water_target_ml INTEGER NOT NULL DEFAULT 2200 CHECK (water_target_ml BETWEEN 500 AND 6000),
  profile_tag TEXT NOT NULL,
  bmi REAL GENERATED ALWAYS AS (
    ROUND(weight_kg / ((height_cm / 100.0) * (height_cm / 100.0)), 2)
  ) STORED,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE
);

-- 天气与环境数据表
CREATE TABLE weather_daily (
  weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
  city TEXT NOT NULL,
  weather_date TEXT NOT NULL,
  temperature_c REAL NOT NULL,
  humidity_pct INTEGER NOT NULL CHECK (humidity_pct BETWEEN 0 AND 100),
  uv_index INTEGER,
  air_quality_index INTEGER,
  heat_risk TEXT NOT NULL CHECK (heat_risk IN ('low', 'medium', 'high', 'extreme')),
  advice TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (city, weather_date)
);

-- 每日养生计划表
CREATE TABLE daily_plan (
  plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  plan_date TEXT NOT NULL,
  breakfast_advice TEXT NOT NULL,
  midday_advice TEXT NOT NULL,
  exercise_advice TEXT NOT NULL,
  evening_advice TEXT NOT NULL,
  health_target_score INTEGER CHECK (health_target_score BETWEEN 0 AND 100),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, plan_date),
  FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE
);

-- 食物库表
CREATE TABLE food_library (
  food_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  calorie_kcal REAL NOT NULL,
  protein_g REAL NOT NULL DEFAULT 0,
  water_ml REAL NOT NULL DEFAULT 0,
  category TEXT NOT NULL CHECK (category IN ('fruit', 'vegetable', 'grain', 'protein', 'beverage', 'other')),
  season TEXT NOT NULL DEFAULT 'all' CHECK (season IN ('spring', 'summer', 'autumn', 'winter', 'all')),
  unit_basis TEXT NOT NULL DEFAULT 'per_100g' CHECK (unit_basis IN ('per_100g', 'per_100ml')),
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 饮食记录表
CREATE TABLE food_record (
  record_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  food_id INTEGER NOT NULL,
  meal_type TEXT NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
  amount REAL NOT NULL CHECK (amount > 0),
  amount_unit TEXT NOT NULL CHECK (amount_unit IN ('g', 'ml')),
  intake_date TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE,
  FOREIGN KEY (food_id) REFERENCES food_library (food_id) ON DELETE RESTRICT
);

-- 饮水记录表
CREATE TABLE water_record (
  record_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  amount_ml INTEGER NOT NULL CHECK (amount_ml BETWEEN 50 AND 3000),
  source TEXT NOT NULL DEFAULT 'water' CHECK (source IN ('water', 'tea', 'soup', 'other')),
  intake_time TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE
);

-- 运动记录表
CREATE TABLE sport_record (
  record_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  sport_type TEXT NOT NULL,
  intensity TEXT NOT NULL DEFAULT 'medium' CHECK (intensity IN ('low', 'medium', 'high')),
  duration_min INTEGER NOT NULL CHECK (duration_min BETWEEN 1 AND 1440),
  calories_burned REAL NOT NULL DEFAULT 0,
  record_date TEXT NOT NULL,
  start_time TEXT,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE
);

-- 睡眠记录表
CREATE TABLE sleep_record (
  record_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  sleep_time TEXT NOT NULL,
  wake_time TEXT NOT NULL,
  quality_score INTEGER NOT NULL CHECK (quality_score BETWEEN 0 AND 100),
  record_date TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE,
  CHECK (julianday(wake_time) > julianday(sleep_time))
);

-- 健康社区动态表
CREATE TABLE community_post (
  post_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  content TEXT NOT NULL,
  posted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  likes_count INTEGER NOT NULL DEFAULT 0 CHECK (likes_count >= 0),
  visibility TEXT NOT NULL DEFAULT 'public' CHECK (visibility IN ('public', 'private')),
  status INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1)),
  FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE
);

CREATE INDEX idx_weather_daily_date ON weather_daily (weather_date);
CREATE INDEX idx_daily_plan_date ON daily_plan (plan_date);
CREATE INDEX idx_food_record_user_date ON food_record (user_id, intake_date);
CREATE INDEX idx_food_record_food ON food_record (food_id);
CREATE INDEX idx_water_record_user_time ON water_record (user_id, intake_time);
CREATE INDEX idx_sport_record_user_date ON sport_record (user_id, record_date);
CREATE INDEX idx_sleep_record_user_date ON sleep_record (user_id, record_date);
CREATE INDEX idx_community_post_user_time ON community_post (user_id, posted_at);

CREATE TRIGGER trg_user_account_updated_at
AFTER UPDATE ON user_account
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE user_account
  SET updated_at = CURRENT_TIMESTAMP
  WHERE user_id = OLD.user_id;
END;

CREATE TRIGGER trg_user_profile_updated_at
AFTER UPDATE ON user_profile
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE user_profile
  SET updated_at = CURRENT_TIMESTAMP
  WHERE user_id = OLD.user_id;
END;

CREATE TRIGGER trg_daily_plan_updated_at
AFTER UPDATE ON daily_plan
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE daily_plan
  SET updated_at = CURRENT_TIMESTAMP
  WHERE plan_id = OLD.plan_id;
END;

CREATE TRIGGER trg_food_library_updated_at
AFTER UPDATE ON food_library
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE food_library
  SET updated_at = CURRENT_TIMESTAMP
  WHERE food_id = OLD.food_id;
END;
