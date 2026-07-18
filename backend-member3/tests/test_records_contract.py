import pytest


def error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


@pytest.fixture
def second_user(client):
    body = {"username": "second_user", "password": "a-secure-password", "nickname": "Second", "profile": {"age": 25, "gender": "male", "heightCm": 175, "weightKg": 70, "goal": "maintain", "activityLevel": "medium", "avgSleepHours": 7, "profileTag": "second"}}
    response = client.post("/api/v1/auth/register", json=body)
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


@pytest.mark.parametrize(
    ("path", "payload", "expected"),
    [
        ("food-records", {"foodId": 1, "mealType": "breakfast", "amount": 100, "amountUnit": "g", "intakeDate": "2026-07-17"}, 201),
        ("water-records", {"amountMl": 50, "intakeTime": "2026-07-17 08:00:00"}, 201),
        ("sport-records", {"sportType": "跑步", "durationMin": 1, "recordDate": "2026-07-17"}, 201),
        ("sleep-records", {"sleepTime": "2026-07-16 23:00:00", "wakeTime": "2026-07-17 07:00:00", "qualityScore": 0, "recordDate": "2026-07-17"}, 201),
    ],
)
def test_record_lifecycle_and_owner_isolation(client, connection, authenticated, second_user, path, payload, expected):
    if path == "food-records":
        connection.execute("INSERT INTO food_library (food_id, name, calorie_kcal, protein_g, water_ml, category, season, unit_basis) VALUES (1, 'Apple', 52, 0, 86, 'fruit', 'all', 'per_100g')")
        connection.commit()
    created = client.post(f"/api/v1/{path}", headers=authenticated, json=payload)
    assert created.status_code == expected, created.text
    record_id = created.json()["data"]["id"]
    assert client.get(f"/api/v1/{path}/{record_id}", headers=authenticated).status_code == 200
    error(client.get(f"/api/v1/{path}/{record_id}", headers=second_user), 404, "RESOURCE_NOT_FOUND")
    error(client.patch(f"/api/v1/{path}/{record_id}", headers=authenticated, json={}), 400, "VALIDATION_ERROR")
    deleted = client.delete(f"/api/v1/{path}/{record_id}", headers=authenticated)
    assert deleted.status_code == 204
    error(client.get(f"/api/v1/{path}/{record_id}", headers=authenticated), 404, "RESOURCE_NOT_FOUND")


def test_record_date_queries_and_domain_boundaries(client, authenticated):
    invalid_water = client.post("/api/v1/water-records", headers=authenticated, json={"amountMl": 49, "intakeTime": "2026-07-17 08:00:00"})
    error(invalid_water, 400, "VALIDATION_ERROR")
    invalid_range = client.get("/api/v1/water-records", headers=authenticated, params={"date": "2026-07-17", "from": "2026-07-01", "to": "2026-07-17"})
    error(invalid_range, 400, "VALIDATION_ERROR")
    invalid_sleep = client.post("/api/v1/sleep-records", headers=authenticated, json={"sleepTime": "2026-07-16 23:00:00", "wakeTime": "2026-07-17 07:00:00", "qualityScore": 100, "recordDate": "2026-07-16"})
    error(invalid_sleep, 400, "VALIDATION_ERROR")
