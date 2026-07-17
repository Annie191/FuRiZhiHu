"""数据库连接 & 统一响应格式"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "furicare.db"


def get_db() -> sqlite3.Connection:
    """获取 SQLite 连接（Row 工厂 = 字典式访问）"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def success(data, msg: str = "ok") -> dict:
    return {"code": 0, "msg": msg, "data": data}


def fail(msg: str, code: int = 1) -> dict:
    return {"code": code, "msg": msg, "data": None}
