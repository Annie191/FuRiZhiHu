from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


def open_connection(database_path: str | Path) -> sqlite3.Connection:
    path = str(database_path)
    connection = sqlite3.connect(path, timeout=5, isolation_level=None, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def database_dependency(database_path: str | Path):
    def get_connection() -> Generator[sqlite3.Connection, None, None]:
        connection = open_connection(database_path)
        try:
            yield connection
        finally:
            connection.close()

    return get_connection


@contextmanager
def transaction(connection: sqlite3.Connection):
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
