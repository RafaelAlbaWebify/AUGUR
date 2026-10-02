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


def test_evidence_status_reports_country_and_esco_coverage():
    with TestClient(app) as client:
        response = client.get("/api/evidence/status")

    assert response.status_code == 200
    body = response.json()

    assert "esco" in body
    assert "mode" in body["esco"]
    assert len(body["countries"]) >= 3

    spain = next(
        item
        for item in body["countries"]
        if item["country_iso3"] == "ESP"
    )
    assert "observed_indicators" in spain
    assert "official_forecast_rows" in spain
    assert "labour_earnings" in spain
    assert "isco_group_count" in spain["labour_earnings"]


def test_operability_endpoint_reports_readiness_and_blockers():
    with TestClient(app) as client:
        response = client.get("/api/operability")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] in {"empty", "partial", "ready"}
    assert isinstance(body["ready"], bool)
    assert "country_analysis_ready" in body
    assert "local_employment_evidence_ready" in body
    assert "esco_full_ready" in body
    assert "personal_fit_full_evidence_ready" in body
    assert isinstance(body["blockers"], list)
    assert "evidence" in body
    assert "esco" in body
