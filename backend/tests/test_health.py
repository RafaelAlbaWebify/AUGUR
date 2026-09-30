from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["phase"] == 0
    assert body["datastores"]["sqlite"] is True
    assert body["datastores"]["duckdb"] is True
