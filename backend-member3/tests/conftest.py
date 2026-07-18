from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
ROOT = SERVICE_ROOT.parent
sys.path.insert(0, str(SERVICE_ROOT))

from app.config import Settings
from app.main import create_app


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "fucare-test.db"
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript((ROOT / "database/01_schema.sql").read_text(encoding="utf-8"))
    db.executescript((ROOT / "database/03_views_and_queries.sql").read_text(encoding="utf-8"))
    db.close()
    return path


@pytest.fixture
def connection(database_path):
    db = sqlite3.connect(database_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    yield db
    db.close()


@pytest.fixture
def client(database_path):
    settings = Settings(NODE_ENV="test", JWT_SECRET="test-secret-with-at-least-16-chars", DATABASE_PATH=str(database_path))
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def registration():
    return {"username": "health_user", "password": "a-secure-password", "nickname": "健康同学", "phone": "13800138003", "email": "health@example.com", "profile": {"age": 24, "gender": "female", "heightCm": 165, "weightKg": 55, "goal": "maintain", "activityLevel": "medium", "avgSleepHours": 7.5, "waterTargetMl": 2100, "profileTag": "稳定作息型用户"}}


@pytest.fixture
def authenticated(client, registration):
    response = client.post("/api/v1/auth/register", json=registration)
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}
