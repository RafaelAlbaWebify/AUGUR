from types import SimpleNamespace

from app.db import analytics
from scripts import accept_g2_local_data_layer as acceptance


def test_acceptance_rejects_missing_database(tmp_path):
    try:
        acceptance.verify(tmp_path / "not-found.duckdb")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Missing database must fail closed")


def test_acceptance_restores_settings_on_query_error(monkeypatch, tmp_path):
    db = tmp_path / "bad.duckdb"
    db.write_bytes(b"invalid DuckDB")
    original = analytics.settings
    try:
        acceptance.verify(db)
    except Exception:
        pass
    else:
        raise AssertionError("Invalid database must fail")
    assert analytics.settings is original


def test_g2_acceptance_against_isolated_duckdb_fixture(monkeypatch, tmp_path):
    from datetime import datetime, timezone

    db = tmp_path / "fixture.duckdb"
    monkeypatch.setattr(analytics, "settings", SimpleNamespace(duckdb_path=db))
    analytics.initialize_analytics_schema()

    base = {
        "geo_level": "nuts2", "indicator_id": "employment",
        "period": 2025, "value": 70.0, "unit": "percent",
        "source_id": "EUROSTAT", "dataset_id": "lfst_r_lfe2emprt",
        "retrieved_at": datetime.now(timezone.utc),
    }
    rows = []
    for i in range(172):
        rows.append({**base, "geo_code": "IE01", "period": 1800 + i,
                     "geography_system": "NUTS_UNSPECIFIED"})
    rows.append({**base, "geo_code": "ES12", "geography_system": "NUTS_2024"})
    # Standalone fixture rows are deliberately synthetic, never source evidence.
    for i in range(1827 - len(rows)):
        rows.append({**base, "geo_code": "ES12", "indicator_id": f"fixture_{i}",
                     "geography_system": "NUTS_UNSPECIFIED"})
    analytics.upsert_subnational_observations(rows)
    analytics.upsert_geographies([{
        "geo_id": "NUTS_2024:IE04", "country_iso3": "IRL", "country_iso2": "IE",
        "geo_level": "nuts2", "geography_system": "NUTS_2024",
        "source_id": "GISCO", "source_geo_code": "IE04",
    }])
    report = acceptance.verify(db)
    assert report["passed"], report["failures"]
    assert report["results"]["retired_code_unverified_observations"] == 172
    assert report["results"]["stored_observation_count"] == 1827
