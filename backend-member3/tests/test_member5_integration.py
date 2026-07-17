from __future__ import annotations

import os
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
ROOT = SERVICE_ROOT.parent
sys.path.insert(0, str(SERVICE_ROOT))

from app.config import Settings
from app.main import create_app

MEMBER5 = ROOT / "backend-member5"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_service(url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise AssertionError(f"Member 5 service stopped during startup:\n{output}")
        try:
            if httpx.get(url, timeout=0.5).status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.1)
    raise AssertionError("Member 5 service did not start within 15 seconds.")


def test_member3_writes_are_visible_to_member5(tmp_path):
    database_path = tmp_path / "member3-member5.e2e.db"
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    for script in ("01_schema.sql", "02_seed.sql", "03_views_and_queries.sql"):
        connection.executescript((ROOT / "database" / script).read_text(encoding="utf-8"))
    connection.close()

    settings = Settings(NODE_ENV="test", JWT_SECRET="integration-secret-at-least-16-chars", DATABASE_PATH=str(database_path))
    app = create_app(settings)
    with TestClient(app) as member3:
        registration = member3.post("/api/v1/auth/register", json={
            "username": "member3_e2e_user",
            "password": "integration-password-123",
            "nickname": "Integration User",
            "profile": {"age": 22, "gender": "male", "heightCm": 175, "weightKg": 70, "goal": "maintain", "activityLevel": "medium", "avgSleepHours": 7, "waterTargetMl": 2200, "profileTag": "integration"},
        })
        assert registration.status_code == 201, registration.text
        user_id = registration.json()["data"]["user"]["id"]
        headers = {"Authorization": f"Bearer {registration.json()['data']['accessToken']}"}

        for path, body in (
            ("water-records", {"amountMl": 1000, "source": "water", "intakeTime": "2026-07-17 10:00:00"}),
            ("sport-records", {"sportType": "running", "durationMin": 30, "caloriesBurned": 200, "recordDate": "2026-07-17"}),
            ("sleep-records", {"sleepTime": "2026-07-16 23:00:00", "wakeTime": "2026-07-17 07:00:00", "qualityScore": 85, "recordDate": "2026-07-17"}),
        ):
            response = member3.post(f"/api/v1/{path}", headers=headers, json=body)
            assert response.status_code == 201, response.text

    port = free_port()
    environment = {**os.environ, "DATABASE_PATH": str(database_path)}
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=MEMBER5,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        wait_for_service(f"{base_url}/", process)
        response = httpx.get(f"{base_url}/api/statistics/{user_id}/overview", params={"date": "2026-07-17"}, timeout=5)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["task_completion"]["water"]["current_ml"] == 1000
        assert body["data"]["task_completion"]["sport"]["current_min"] == 30
        assert body["data"]["task_completion"]["sleep"]["quality_score"] == 85
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
