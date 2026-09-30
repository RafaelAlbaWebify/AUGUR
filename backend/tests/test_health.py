from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["phase"] == 1
    assert body["datastores"]["sqlite"] is True
    assert body["datastores"]["duckdb"] is True


def test_country_registry_contains_spain():
    with TestClient(app) as client:
        response = client.get("/api/countries")

    assert response.status_code == 200
    countries = response.json()["countries"]
    assert any(country["iso3"] == "ESP" for country in countries)


def test_spain_snapshot_is_available_before_sync():
    with TestClient(app) as client:
        response = client.get("/api/countries/ESP/snapshot")

    assert response.status_code == 200
    assert response.json()["country_iso3"] == "ESP"
