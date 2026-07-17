# 伏日智护数据库协作说明

这份文档提供给其余成员使用，目的是让前端、接口、推荐、画像分析几位同学可以直接基于当前数据库配置开展工作。

## 1. 数据库现状

- 数据库类型：`SQLite`
- 数据库文件：`database/furicare.db`
- 初始化脚本：
  - `database/01_schema.sql`
  - `database/02_seed.sql`
  - `database/03_views_and_queries.sql`
- 一键初始化命令：

```powershell
python database\init_sqlite.py
```

如果数据库文件需要重建，重新执行上面的命令即可。

## 2. 目录说明

- `01_schema.sql`：表结构、外键、索引、触发器
- `02_seed.sql`：演示测试数据
- `03_views_and_queries.sql`：统计视图和联调查询示例
- `furicare.db`：当前本地数据库文件
- `test_database_usage.py`：从其他四位成员角度出发的数据库测试

## 3. 当前核心表

- `user_account`：用户账号主表
- `user_profile`：用户健康画像
- `daily_plan`：每日养生计划
- `weather_daily`：天气与环境数据
- `food_library`：食物库
- `food_record`：饮食记录
- `water_record`：饮水记录
- `sport_record`：运动记录
- `sleep_record`：睡眠记录
- `community_post`：社区动态

## 4. 当前可直接使用的统计视图

- `v_daily_food_summary`：每日饮食营养汇总
- `v_daily_water_summary`：每日饮水汇总
- `v_daily_sport_summary`：每日运动汇总
- `v_daily_sleep_summary`：每日睡眠汇总
- `v_dashboard_daily`：首页健康总览汇总

建议优先查视图，而不是每次自己拼多表统计。

## 5. 给成员 1 的说明：前端如何接数据库结果

成员 1 负责首页、公共布局和图表展示，可以优先使用下面这些数据来源：

- 首页 Dashboard：`v_dashboard_daily + user_account + user_profile + weather_daily + daily_plan`
- 运动趋势图：`v_daily_sport_summary`
- 睡眠趋势图：`v_daily_sleep_summary`
- 饮食统计卡片：`v_daily_food_summary`
- 社区动态列表：`community_post + user_account`

首页建议字段：

- `nickname`
- `health_score`
- `water_ml`
- `water_target_ml`
- `sport_duration_min`
- `food_calorie_kcal`
- `sleep_quality_score`
- `temperature_c`
- `humidity_pct`
- `heat_risk`
- `advice`
- `breakfast_advice`
- `midday_advice`
- `exercise_advice`
- `evening_advice`

前端联调建议：

- 先固定用户 `user_id = 1`
- 先固定日期 `2026-07-17`
- 先做静态页面绑定，再切换为接口返回

## 6. 给成员 3 的说明：接口层如何接数据库

成员 3 负责 Node.js + Express 接口，可以把数据库作为单机本地文件使用。

建议接口分组：

- 用户模块
  - 查询用户基本信息：`user_account`
  - 查询健康档案：`user_profile`
- 首页模块
  - 查询首页总览：`v_dashboard_daily`
  - 查询当日计划：`daily_plan`
  - 查询天气风险：`weather_daily`
- 饮食模块
  - 查询食物库：`food_library`
  - 新增饮食记录：`food_record`
  - 查询每日饮食汇总：`v_daily_food_summary`
- 饮水模块
  - 新增饮水记录：`water_record`
  - 查询饮水汇总：`v_daily_water_summary`
- 运动模块
  - 新增运动记录：`sport_record`
  - 查询运动趋势：`v_daily_sport_summary`
- 睡眠模块
  - 新增睡眠记录：`sleep_record`
  - 查询睡眠趋势：`v_daily_sleep_summary`
- 社区模块
  - 发布动态：`community_post`
  - 查询动态：`community_post + user_account`

接口开发注意点：

- 必须开启 SQLite 外键约束
- 写入记录前先确认 `user_id` 是否存在
- `daily_plan` 存在 `(user_id, plan_date)` 唯一约束，同一天同一用户不能重复写计划
- `user_account.username`、`phone`、`email` 都有唯一约束

如果使用 Node.js，建议初始化连接后执行：

```sql
PRAGMA foreign_keys = ON;
```

## 7. 给成员 4 的说明：推荐规则如何接数据库

成员 4 负责健康评分、天气处理和计划生成，可以直接依赖现有数据表和视图。

推荐逻辑可用输入：

- 用户基础画像：`user_profile`
- 天气环境：`weather_daily`
- 饮水情况：`v_daily_water_summary`
- 饮食情况：`v_daily_food_summary`
- 运动情况：`v_daily_sport_summary`
- 睡眠情况：`v_daily_sleep_summary`

推荐逻辑可写回：

- 每日计划结果写入 `daily_plan`
- 新天气数据写入 `weather_daily`

当前健康分公式已经体现在 `v_dashboard_daily`：

```text
饮水完成度 * 30
+ 运动完成度 * 25
+ 饮食健康度 * 25
+ 睡眠质量 * 20
```

成员 4 可以直接：

- 复用当前健康分
- 或在接口层读取原始统计值后自行扩展规则

建议流程：

1. 读取用户画像
2. 读取当天天气
3. 读取近 1 天或近 3 天行为数据
4. 生成计划文案
5. 写入 `daily_plan`

## 8. 给成员 5 的说明：画像分析如何接数据库

成员 5 负责健康画像分析、健康报告和趋势统计，可以直接基于已有字段和统计视图做分析。

可直接用的画像字段：

- `age`
- `gender`
- `height_cm`
- `weight_kg`
- `bmi`
- `goal`
- `activity_level`
- `avg_sleep_hours`
- `water_target_ml`
- `profile_tag`

可直接用的分析数据：

- 饮食营养：`v_daily_food_summary`
- 饮水习惯：`v_daily_water_summary`
- 运动趋势：`v_daily_sport_summary`
- 睡眠趋势：`v_daily_sleep_summary`
- 综合健康：`v_dashboard_daily`

适合做的报告指标：

- BMI 状态
- 近 7 天平均睡眠评分
- 近 7 天总运动时长
- 当日或近 7 天平均饮水量
- 健康分趋势
- 用户画像标签说明

## 9. 日期与字段约定

为了减少联调问题，当前约定如下：

- 日期字段统一用 `TEXT` 存储，格式使用 `YYYY-MM-DD`
- 时间字段统一用 `TEXT` 存储，格式使用 `HH:MM:SS`
- 日期时间字段统一用 `TEXT` 存储，格式使用 `YYYY-MM-DD HH:MM:SS`

常见字段含义：

- `goal`
  - `lose_fat`：减脂
  - `maintain`：保持健康
  - `gain_muscle`：增肌
- `activity_level`
  - `low`：较少运动
  - `medium`：中等运动
  - `high`：高频运动
- `status`
  - 在 `daily_plan` 中：`pending` / `completed`
  - 在 `community_post` 中：`1` 正常，`0` 隐藏

## 10. 联调建议顺序

推荐大家按下面顺序接入数据库：

1. 成员 3 先把数据库连接与基础查询接口打通
2. 成员 1 用固定用户和固定日期先接首页展示
3. 成员 4 再接天气写入和计划生成
4. 成员 5 最后接画像分析与趋势统计

这样可以最大程度减少同时改库带来的冲突。

## 11. 已完成的数据库验证

已经有自动化测试脚本覆盖以下场景：

- 前端首页展示所需数据能否查出
- 接口层能否新增用户和行为记录
- 约束是否能拦住非法写入
- 推荐规则能否读取汇总数据并写回计划
- 画像分析能否直接读取 BMI 和行为统计

运行方式：

```powershell
python database\test_database_usage.py
```

## 12. 协作注意事项

- 不要手动改 `furicare.db` 里的结构，结构变更统一修改 `01_schema.sql`
- 新增测试数据优先补到 `02_seed.sql`
- 新增统计查询优先补到 `03_views_and_queries.sql`
- 如果后续需要换成 MySQL，可以先保持字段命名不变，后期迁移会更容易

如果其他成员只想快速开始开发，最少只需要做两步：

```powershell
python database\init_sqlite.py
python database\test_database_usage.py
```

第一步生成数据库，第二步确认数据库可用。
