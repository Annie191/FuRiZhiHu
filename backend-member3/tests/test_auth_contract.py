import pytest


def error(response, status, code):
    assert response.status_code == status, response.text
    body = response.json()["error"]
    assert body["code"] == code
    assert "message" in body
    assert "details" in body


def test_registration_rejects_unknown_fields_and_invalid_username(client, registration):
    error(client.post("/api/v1/auth/register", json={**registration, "unexpected": True}), 400, "VALIDATION_ERROR")
    error(client.post("/api/v1/auth/register", json={**registration, "username": "bad name"}), 400, "VALIDATION_ERROR")


@pytest.mark.parametrize("field,value", [("username", "health_user"), ("phone", "13800138003"), ("email", "HEALTH@EXAMPLE.COM")])
def test_registration_identifier_collisions_are_atomic(client, connection, registration, field, value):
    assert client.post("/api/v1/auth/register", json=registration).status_code == 201
    duplicate = {**registration, "username": "other_user", "phone": "13900139003", "email": "other@example.com"}
    duplicate[field] = value
    error(client.post("/api/v1/auth/register", json=duplicate), 409, "ACCOUNT_IDENTIFIER_TAKEN")
    assert connection.execute("SELECT COUNT(*) FROM user_account").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM user_profile").fetchone()[0] == 1


@pytest.mark.parametrize("identifier_key", ["username", "phone", "email"])
def test_login_accepts_each_identifier(client, registration, identifier_key):
    assert client.post("/api/v1/auth/register", json=registration).status_code == 201
    response = client.post("/api/v1/auth/login", json={"identifier": registration[identifier_key], "password": registration["password"]})
    assert response.status_code == 200
    assert response.json()["data"]["user"]["username"] == registration["username"]


def test_credential_failures_share_one_response(client, connection, registration):
    assert client.post("/api/v1/auth/register", json=registration).status_code == 201
    wrong = client.post("/api/v1/auth/login", json={"identifier": registration["username"], "password": "wrong-password"})
    missing = client.post("/api/v1/auth/login", json={"identifier": "nobody", "password": "wrong-password"})
    connection.execute("UPDATE user_account SET status = 0 WHERE username = ?", (registration["username"],))
    connection.commit()
    disabled = client.post("/api/v1/auth/login", json={"identifier": registration["username"], "password": registration["password"]})
    assert wrong.status_code == missing.status_code == disabled.status_code == 401
    assert wrong.json() == missing.json() == disabled.json()


def test_current_user_rejects_missing_tampered_and_disabled_tokens(client, connection, registration):
    token = client.post("/api/v1/auth/register", json=registration).json()["data"]["accessToken"]
    error(client.get("/api/v1/auth/me"), 401, "AUTH_REQUIRED")
    error(client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}broken"}), 401, "INVALID_TOKEN")
    connection.execute("UPDATE user_account SET status = 0 WHERE username = ?", (registration["username"],))
    connection.commit()
    error(client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}), 401, "INVALID_TOKEN")
