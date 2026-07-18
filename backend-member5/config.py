"""数据库连接 & 统一响应格式"""

import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_database_path() -> Path:
    configured = Path(os.getenv("DATABASE_PATH", "database/furicare.db"))
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


def get_db() -> sqlite3.Connection:
    """获取 SQLite 连接（Row 工厂 = 字典式访问）"""
    path = resolve_database_path()
    if not path.exists():
        raise RuntimeError(f"Database file does not exist: {path}")
    conn = sqlite3.connect(str(path), timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def success(data, msg: str = "ok") -> dict:
    return {"code": 0, "msg": msg, "data": data}


def fail(msg: str, code: int = 1) -> dict:
    return {"code": code, "msg": msg, "data": None}
