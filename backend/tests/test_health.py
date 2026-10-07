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
    assert "source_ids" in spain
    assert "labour_earnings" in spain
    assert "isco_group_count" in spain["labour_earnings"]
    assert "net_earnings" in spain
    assert "row_count" in spain["net_earnings"]
    assert "job_transitions" in spain
    assert "age_group_count" in spain["job_transitions"]
    assert "job_vacancies" in spain
    assert "isco_group_count" in spain["job_vacancies"]


def test_operability_endpoint_reports_readiness_and_blockers():
    with TestClient(app) as client:
        response = client.get("/api/operability")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] in {"empty", "partial", "ready"}
    assert isinstance(body["ready"], bool)
    assert "analysis_ready" in body
    assert "ttv_temporal_model_ready" in body
    assert "ttv_temporal_model_version" in body
    assert "ttv_temporal_validation" in body
    assert "ttv_calibration" in body
    assert "infrastructure_ready" in body["ttv_calibration"]
    assert "externally_calibrated" in body["ttv_calibration"]
    assert "protocol_state" in body["ttv_calibration"]
    assert body["ttv_calibration"]["protocol_state"] == "definitions_frozen_acceptance_pending"
    assert body["ttv_calibration"]["protocol_version"] is None
    assert body["ttv_calibration"]["protocol_ready_for_holdout"] is False
    assert "development_case_count" in body["ttv_calibration"]
    assert "holdout_case_count" in body["ttv_calibration"]
    assert body["ttv_calibration"]["protocol_document"] == "docs/TTV_CALIBRATION_PROTOCOL.md"
    assert "protocol_readiness" in body["ttv_calibration"]
    assert body["ttv_calibration"]["protocol_readiness"]["ready_for_holdout_collection"] is False
    assert "start_event_definition" in body["ttv_calibration"]["protocol_readiness"]["blockers"]
    assert "ready_for_versioning" in body["ttv_temporal_validation"]
    assert "gates" in body["ttv_temporal_validation"]
    assert "country_analysis_ready" in body
    assert "local_employment_evidence_ready" in body
    assert "job_transition_evidence_ready" in body
    assert "esco_full_ready" in body
    assert "personal_fit_core_evidence_ready" in body
    assert "personal_fit_full_evidence_ready" in body
    assert "career_market_evidence" in body
    assert isinstance(body["blockers"], list)
    assert "evidence" in body
    assert "esco" in body


def test_overview_series_endpoint_returns_observed_history():
    with TestClient(app) as client:
        response = client.get("/api/countries/ESP/overview-series")

    assert response.status_code == 200
    body = response.json()

    assert body["country_iso3"] == "ESP"
    assert isinstance(body["series"], list)

    for item in body["series"]:
        assert "indicator_id" in item
        assert "points" in item
        assert len(item["points"]) <= 8
        periods = [point["period"] for point in item["points"]]
        assert periods == sorted(periods)
