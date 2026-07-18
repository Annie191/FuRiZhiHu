def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "fucare-api", "database": "ok"}


def test_registration_login_and_current_user(client, connection, registration):
    registered = client.post("/api/v1/auth/register", json=registration)
    assert registered.status_code == 201
    body = registered.json()["data"]
    assert body["tokenType"] == "Bearer"
    assert body["user"]["profile"]["bmi"] == 20.2
    assert connection.execute("SELECT COUNT(*) FROM user_profile").fetchone()[0] == 1

    login = client.post("/api/v1/auth/login", json={"identifier": registration["email"], "password": registration["password"]})
    assert login.status_code == 200
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login.json()['data']['accessToken']}"})
    assert me.status_code == 200
    assert me.json()["data"]["user"]["username"] == registration["username"]


def test_duplicate_registration_is_atomic(client, connection, registration):
    assert client.post("/api/v1/auth/register", json=registration).status_code == 201
    duplicate = client.post("/api/v1/auth/register", json={**registration, "username": "other_user"})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "ACCOUNT_IDENTIFIER_TAKEN"
    assert connection.execute("SELECT COUNT(*) FROM user_account").fetchone()[0] == 1


def test_profile_and_record_ownership(client, connection, authenticated):
    profile = client.patch("/api/v1/profile", headers=authenticated, json={"weightKg": 60})
    assert profile.status_code == 200
    assert profile.json()["data"]["bmi"] == 22.04

    water = client.post("/api/v1/water-records", headers=authenticated, json={"amountMl": 250, "intakeTime": "2026-07-17 08:00:00"})
    assert water.status_code == 201
    summary = client.get("/api/v1/water-records/daily-summary", headers=authenticated, params={"date": "2026-07-17"})
    assert summary.status_code == 200
    assert summary.json()["data"][0]["totalWaterMl"] == 250


def test_validation_and_not_found_envelopes(client):
    bad = client.post("/api/v1/auth/register", json={})
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "VALIDATION_ERROR"
    missing = client.get("/api/v1/not-here")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_foods_and_all_record_types(client, connection, authenticated):
    connection.execute("INSERT INTO food_library (name, calorie_kcal, protein_g, water_ml, category, season, unit_basis) VALUES (?, ?, ?, ?, ?, ?, ?)", ("苹果", 52, 0.3, 86, "fruit", "autumn", "per_100g"))
    connection.commit()

    foods = client.get("/api/v1/foods", params={"category": "fruit"})
    assert foods.status_code == 200
    food_id = foods.json()["data"]["items"][0]["id"]

    food = client.post("/api/v1/food-records", headers=authenticated, json={"foodId": food_id, "mealType": "breakfast", "amount": 100, "amountUnit": "g", "intakeDate": "2026-07-17"})
    sport = client.post("/api/v1/sport-records", headers=authenticated, json={"sportType": "跑步", "durationMin": 30, "recordDate": "2026-07-17"})
    sleep = client.post("/api/v1/sleep-records", headers=authenticated, json={"sleepTime": "2026-07-16 23:00:00", "wakeTime": "2026-07-17 07:00:00", "qualityScore": 85, "recordDate": "2026-07-17"})
    assert food.status_code == sport.status_code == sleep.status_code == 201

    assert client.get("/api/v1/food-records/daily-summary", headers=authenticated, params={"date": "2026-07-17"}).json()["data"][0]["totalCalorieKcal"] == 52
    assert client.get("/api/v1/sport-records/daily-summary", headers=authenticated, params={"date": "2026-07-17"}).json()["data"][0]["totalDurationMin"] == 30
    assert client.get("/api/v1/sleep-records/daily-summary", headers=authenticated, params={"date": "2026-07-17"}).json()["data"][0]["sleepHours"] == 8


def test_record_domain_validation(client, authenticated):
    invalid_sleep = client.post("/api/v1/sleep-records", headers=authenticated, json={"sleepTime": "2026-07-17 08:00:00", "wakeTime": "2026-07-17 07:00:00", "qualityScore": 70, "recordDate": "2026-07-17"})
    assert invalid_sleep.status_code == 400
    assert invalid_sleep.json()["error"]["code"] == "VALIDATION_ERROR"
