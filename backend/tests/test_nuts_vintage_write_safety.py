from datetime import datetime, timezone
from types import SimpleNamespace

from app.db import analytics
from app.services import regional_evidence as regional


def observation(code="IE01", system=None):
    row = {
        "geo_code": code,
        "geo_name": code,
        "geo_level": "NUTS2",
        "indicator_id": "regional_employment_rate",
        "period": 2025,
        "value": 70.0,
        "unit": "percent",
        "source_id": "EUROSTAT",
        "dataset_id": "lfst_r_lfe2emprt",
        "retrieved_at": datetime.now(timezone.utc),
        "source_updated_at": "2026-09-10",
    }
    if system is not None:
        row["geography_system"] = system
    return row


def test_unversioned_nuts_observation_is_not_promoted_to_nuts2024(monkeypatch, tmp_path):
    path = tmp_path / "nuts-vintage.duckdb"
    monkeypatch.setattr(analytics, "settings", SimpleNamespace(duckdb_path=path))
    analytics.initialize_analytics_schema()

    assert analytics.upsert_subnational_observations([observation()]) == 1

    rows = analytics.latest_subnational_observations("IE01")
    assert len(rows) == 1
    assert rows[0]["geography_system"] == "NUTS_UNSPECIFIED"

    # Evidence alone must not manufacture a current territorial registry row.
    assert analytics.geography_records_by_source_codes(["IE01"]) == []


def test_explicit_geography_system_remains_explicit(monkeypatch, tmp_path):
    path = tmp_path / "explicit-vintage.duckdb"
    monkeypatch.setattr(analytics, "settings", SimpleNamespace(duckdb_path=path))
    analytics.initialize_analytics_schema()

    analytics.upsert_subnational_observations([
        observation(code="ES12", system="NUTS_2024")
    ])

    rows = analytics.latest_subnational_observations(
        "ES12",
        geography_system="NUTS_2024",
    )
    assert len(rows) == 1
    assert rows[0]["geography_system"] == "NUTS_2024"
    registry = analytics.geography_records_by_source_codes(["ES12"])
    assert len(registry) == 1
    assert registry[0]["geography_system"] == "NUTS_2024"


def test_current_registry_counts_same_code_unverified_observations(monkeypatch, tmp_path):
    path = tmp_path / "registry-evidence.duckdb"
    monkeypatch.setattr(analytics, "settings", SimpleNamespace(duckdb_path=path))
    analytics.initialize_analytics_schema()

    analytics.upsert_subnational_observations([observation(code="ES12")])
    analytics.upsert_geographies([
        {
            "geo_id": "NUTS_2024:ES12",
            "country_iso3": "ESP",
            "country_iso2": "ES",
            "name": "Principado de Asturias",
            "geo_level": "nuts2",
            "geography_system": "NUTS_2024",
            "source_id": "GISCO",
            "source_geo_code": "ES12",
        }
    ])

    rows = analytics.geographies_for_country("ESP")
    current = [row for row in rows if row["geo_id"] == "NUTS_2024:ES12"]
    assert len(current) == 1
    assert current[0]["indicator_count"] == 1
    assert current[0]["latest_period"] == 2025

    coverage = analytics.geography_coverage_status()
    item = next(
        row for row in coverage["coverage"]
        if row["geography_system"] == "NUTS_2024"
        and row["geo_level"] == "nuts2"
    )
    assert item["analysis_status"] == "available"
    assert item["observation_count"] == 1


def test_current_nuts_read_falls_back_to_same_code_unverified_vintage(monkeypatch):
    calls = []

    def fake_bundle(code, max_history_points=8, geography_system=None):
        calls.append(geography_system)
        if geography_system == "NUTS_2024":
            return {
                "latest": [],
                "history": [],
                "sectors": [],
                "environmental_health": [],
            }
        assert geography_system == "NUTS_UNSPECIFIED"
        return {
            "latest": [observation(code=code)],
            "history": [],
            "sectors": [],
            "environmental_health": [],
        }

    monkeypatch.setattr(regional, "regional_evidence_bundle", fake_bundle)
    monkeypatch.setattr(
        regional,
        "_regional_result_from_local",
        lambda code, rows, **kwargs: {
            "geography_system": rows[0].get("geography_system", "NUTS_UNSPECIFIED"),
            "geo_code": code,
            "notes": [],
        } if rows else None,
    )
    regional._REGIONAL_CACHE.clear()

    result = regional.regional_evidence(
        "ES12",
        geography_system="NUTS_2024",
    )

    assert calls == ["NUTS_2024", "NUTS_UNSPECIFIED"]
    assert result["requested_geography_system"] == "NUTS_2024"
    assert result["geography_compatibility"] == "same_code_vintage_unverified"
    assert "not asserted as NUTS 2024" in result["notes"][-1]
