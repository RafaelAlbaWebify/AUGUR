"""HTTP comparison acceptance at the real FastAPI router boundary.

Only synthetic fixtures; no local operator database, external network or persistent writes.
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import routes
from app.services.compare import build_comparison
from scripts.check_compare_contract import verify_compare_shape, TS_FILE


def _client(monkeypatch):
    monkeypatch.setattr(routes, "list_countries", lambda: [
        {"iso3": "ESP", "name": "Spain"}, {"iso3": "IRL", "name": "Ireland"},
        {"iso3": "PRT", "name": "Portugal"}])
    def comparison(requested):
        snapshots = {}
        for country in requested:
            snapshots[country] = [{
                "indicator_id": "unemployment_rate",
                "name": "Unemployment rate",
                "dimension": "productive_capacity",
                "unit": "percent",
                "period": 2025 if country == "ESP" else 2024,
                "value": 10.4 if country == "ESP" else 4.7,
                "source_id": "EUROSTAT",
            }]
        return build_comparison(requested, snapshots)
    monkeypatch.setattr(routes, "country_comparison", comparison)
    app = FastAPI()
    app.include_router(routes.router, prefix="/api")
    return TestClient(app)


def test_http_compare_preserves_cross_layer_payload_and_mixed_years(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/api/compare?countries=ESP,IRL")
    assert response.status_code == 200
    payload = response.json()
    assert verify_compare_shape(payload, TS_FILE.read_text(encoding="utf-8")) == []
    assert payload["countries"] == [{"iso3": "ESP", "name": "ESP"}, {"iso3": "IRL", "name": "IRL"}]
    values = payload["indicators"][0]["countries"]
    assert values["ESP"]["period"] == 2025
    assert values["IRL"]["period"] == 2024
    assert values["ESP"]["source_id"] == values["IRL"]["source_id"] == "EUROSTAT"


def test_http_compare_rejects_missing_or_unknown_country_without_500(monkeypatch):
    client = _client(monkeypatch)
    assert client.get("/api/compare?countries=ESP").status_code == 400
    assert client.get("/api/compare?countries=ESP,UNKNOWN").status_code == 404
    assert client.get("/api/compare?countries=ESP,IRL,PRT,ESP,IRL,PRT").status_code == 400
