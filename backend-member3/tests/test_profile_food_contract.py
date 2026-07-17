def error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


def test_profile_requires_authentication_and_recalculates_bmi(client, authenticated):
    error(client.get("/api/v1/profile"), 401, "AUTH_REQUIRED")
    updated = client.patch("/api/v1/profile", headers=authenticated, json={"heightCm": 180, "weightKg": 81})
    assert updated.status_code == 200
    assert updated.json()["data"]["bmi"] == 25


def test_profile_patch_rejects_empty_unknown_and_out_of_range(client, authenticated):
    error(client.patch("/api/v1/profile", headers=authenticated, json={}), 400, "VALIDATION_ERROR")
    error(client.patch("/api/v1/profile", headers=authenticated, json={"unknown": 1}), 400, "VALIDATION_ERROR")
    error(client.patch("/api/v1/profile", headers=authenticated, json={"age": 9}), 400, "VALIDATION_ERROR")


def test_food_list_filter_pagination_and_detail_errors(client, connection):
    connection.executemany("INSERT INTO food_library (name, calorie_kcal, protein_g, water_ml, category, season, unit_basis) VALUES (?, ?, ?, ?, ?, ?, ?)", [("Apple", 52, 0, 86, "fruit", "autumn", "per_100g"), ("Banana", 89, 1, 75, "fruit", "all", "per_100g")])
    connection.commit()
    listed = client.get("/api/v1/foods", params={"q": "a", "category": "fruit", "page": 1, "pageSize": 1})
    assert listed.status_code == 200
    assert listed.json()["data"] == {"items": [listed.json()["data"]["items"][0]], "page": 1, "pageSize": 1, "total": 2}
    assert listed.json()["data"]["items"][0]["name"] == "Apple"
    error(client.get("/api/v1/foods/0"), 400, "VALIDATION_ERROR")
    error(client.get("/api/v1/foods/9999"), 404, "RESOURCE_NOT_FOUND")
    error(client.get("/api/v1/foods", params={"category": "invalid"}), 400, "VALIDATION_ERROR")
