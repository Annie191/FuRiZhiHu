# 数据库交付说明

默认数据库选型为 `SQLite`。

## 文件说明

- `01_schema.sql`：建表、外键、约束、索引、更新时间触发器
- `02_seed.sql`：演示测试数据，方便前后端联调
- `03_views_and_queries.sql`：首页统计视图与常用查询示例
- `init_sqlite.py`：一键初始化本地 `furicare.db`
- `test_database_usage.py`：从成员 1、3、4、5 的使用角度验证数据库是否满足联调需求
- `TEAM_INTEGRATION_GUIDE.md`：提供给其他成员的数据库协作说明文档

## 覆盖模块

- 用户账号与健康画像
- 每日养生计划
- 食物库与饮食记录
- 饮水记录
- 运动记录
- 睡眠记录
- 天气与环境分析
- 健康社区动态

## 初始化方式

如果你本机有 Python 3，直接在项目根目录执行：

```powershell
python database\init_sqlite.py
```

默认会在 `database/furicare.db` 生成 SQLite 数据库文件。

运行数据库测试：

```powershell
python database\test_database_usage.py
```

如果你本机安装了 SQLite 命令行，也可以手动执行：

```powershell
sqlite3 database\furicare.db ".read database/01_schema.sql"
sqlite3 database\furicare.db ".read database/02_seed.sql"
sqlite3 database\furicare.db ".read database/03_views_and_queries.sql"
```

## 设计说明

- 需求文档里只有 `user_profile`，但其他业务表都依赖 `user_id`，因此补充了 `user_account` 作为统一主表。
- 首页包含饮水完成度和天气风险，因此补充了 `water_record` 与 `weather_daily`。
- 每日养生计划需要单独保存，所以增加了 `daily_plan`，便于推荐模块写入结果、接口模块直接读取。
- `v_dashboard_daily` 视图把饮水、运动、饮食、睡眠做了日汇总，并按需求文档中的权重给出基础健康分。
- 原先的 MySQL 专属语法已经替换为 SQLite 兼容写法，适合课程项目本地直接演示。
