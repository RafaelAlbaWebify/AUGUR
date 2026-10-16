"""GR-0 read-only exporter contract tests with actual DuckDB fixtures."""
import duckdb
import pytest
from scripts.export_ranking_evidence_audit import audit


def test_audit_groups_real_rows_by_source_unit_period_without_writes(tmp_path):
    db = tmp_path / "observations.duckdb"
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE observations (country_iso3 VARCHAR, indicator_id VARCHAR, period INTEGER, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR, observation_type VARCHAR)")
    con.execute("CREATE TABLE geography_registry (country_iso3 VARCHAR, geography_system VARCHAR, geo_level VARCHAR, source_geo_code VARCHAR)")
    con.execute("CREATE TABLE subnational_observations (geography_system VARCHAR, geo_level VARCHAR, geo_code VARCHAR, indicator_id VARCHAR, period INTEGER, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR)")
    con.execute("INSERT INTO observations VALUES ('ESP','unemployment_rate',2025,'percent','EUROSTAT','une','observed'), ('PRT','unemployment_rate',2025,'percent','EUROSTAT','une','observed')")
    con.execute("INSERT INTO geography_registry VALUES ('ESP','NUTS_2024','nuts2','ES11'),('ESP','NUTS_2024','nuts2','ES12'),('PRT','NUTS_2024','nuts2','PT11')")
    con.execute("INSERT INTO subnational_observations VALUES ('NUTS_2024','nuts2','ES11','regional_unemployment_rate',2025,'percent','EUROSTAT','labour'),('NUTS_2024','nuts2','ES12','regional_unemployment_rate',2024,'percent','EUROSTAT','labour'),('NUTS_2024','nuts2','PT11','regional_unemployment_rate',2025,'percent','EUROSTAT','labour')")
    con.close()
    before = db.stat().st_size
    output = audit(db, ["esp", "prt"])
    assert output["countries"] == ["ESP", "PRT"]
    assert len(output["national_observations"]) == 2
    assert len(output["subnational_observations"]) == 3
    assert {x["period"] for x in output["subnational_observations"]} == {2024, 2025}
    assert {x["registered_geographies"] for x in output["registered_geography_groups"]} == {1, 2}
    assert not any("value" in row for row in output["subnational_observations"])
    assert db.stat().st_size == before


def test_audit_rejects_invalid_country_codes(tmp_path):
    with pytest.raises(ValueError, match="ISO3"):
        audit(tmp_path / "does_not_matter.duckdb", ["ES"])
