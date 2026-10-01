from fastapi.testclient import TestClient

from app.main import app


def test_empty_profile_is_available():
    with TestClient(app) as client:
        response = client.get("/api/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["profile_id"] == "default"
    assert body["household_size"] >= 1
    assert isinstance(body["citizenships"], list)
    assert isinstance(body["skills"], list)
    assert isinstance(body["languages"], list)


def test_profile_round_trip():
    payload = {
        "age": 40,
        "current_country": "esp",
        "citizenships": ["esp"],
        "profession": "Systems engineer",
        "skills": ["Windows", "Python"],
        "languages": [
            {"language": "Spanish", "cefr": "C2"},
            {"language": "English", "cefr": "B2"},
        ],
        "household_size": 2,
        "monthly_net_income": 3000,
        "liquid_savings": 25000,
        "remote_work": True,
        "preferences": {
            "climate": "temperate",
            "city_size": "medium",
        },
    }

    with TestClient(app) as client:
        saved = client.put("/api/profile", json=payload)
        loaded = client.get("/api/profile")

    assert saved.status_code == 200
    assert loaded.status_code == 200

    body = loaded.json()
    assert body["current_country"] == "ESP"
    assert body["citizenships"] == ["ESP"]
    assert body["profession"] == "Systems engineer"
    assert body["languages"][1]["cefr"] == "B2"
    assert body["remote_work"] is True
    assert body["updated_at"] is not None
