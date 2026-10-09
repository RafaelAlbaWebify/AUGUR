from types import SimpleNamespace
import duckdb
from app.services import geography_provenance as module


def test_geo_provenance_preserves_real_code_identity_and_missing_data(tmp_path, monkeypatch):
    path = tmp_path / "geographies.duckdb"
    con = duckdb.connect(str(path))
    con.execute("""CREATE TABLE geography_registry (
        country_iso3 VARCHAR, geo_id VARCHAR, source_geo_code VARCHAR,
        name VARCHAR, geography_system VARCHAR, geo_level VARCHAR,
        source_id VARCHAR, parent_geo_id VARCHAR
    )""")
    con.execute("""CREATE TABLE subnational_observations (
        geography_system VARCHAR, geo_code VARCHAR, geo_level VARCHAR,
        indicator_id VARCHAR, period INTEGER, source_id VARCHAR, dataset_id VARCHAR
    )""")
    con.executemany("INSERT INTO geography_registry VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        ("ESP", "a", "ES11", "Galicia", "NUTS_2024", "nuts2", "EUROSTAT", None),
        ("ESP", "b", "ES12", "Principado de Asturias", "NUTS_2024", "nuts2", "EUROSTAT", None),
        ("IRL", "c", "IE04", "Ireland test code", "NUTS_2024", "nuts2", "EUROSTAT", None),
    ])
    con.executemany("INSERT INTO subnational_observations VALUES (?, ?, ?, ?, ?, ?, ?)", [
        ("NUTS_2024", "ES11", "nuts2", "regional_population", 2024, "EUROSTAT", "demo_r_pjanaggr3"),
        ("NUTS_2024", "ES11", "nuts2", "regional_population", 2025, "EUROSTAT", "demo_r_pjanaggr3"),
        ("NUTS_2024", "IE04", "nuts2", "regional_population", 2020, "EUROSTAT", "demo_r_pjanaggr3"),
    ])
    con.close()
    monkeypatch.setattr(module, "settings", SimpleNamespace(duckdb_path=path))
    result = module.geography_provenance("esp")
    assert result["registered_geography_count"] == 2
    galicia, asturias = result["items"]
    assert galicia["source_geo_code"] == "ES11"
    assert galicia["observed_indicator_count"] == 1
    assert galicia["observed_period_count"] == 2
    assert galicia["last_observed_period"] == 2025
    assert galicia["dataset_ids"] == ["demo_r_pjanaggr3"]
    assert galicia["boundary_version_verified"] is False
    assert asturias["has_evidence"] is False
    assert asturias["last_observed_period"] is None
    assert asturias["indicator_ids"] == []
