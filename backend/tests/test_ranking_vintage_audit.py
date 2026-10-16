import duckdb
from scripts.export_ranking_vintage_audit import build_report


def test_exact_identities_without_values_or_claims(tmp_path):
    path = tmp_path / "test.duckdb"
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE geography_registry (geo_id VARCHAR, country_iso3 VARCHAR, source_geo_code VARCHAR, name VARCHAR, geography_system VARCHAR, geo_level VARCHAR)")
    con.execute("CREATE TABLE subnational_observations (geography_system VARCHAR, geo_code VARCHAR, geo_level VARCHAR, indicator_id VARCHAR, period INTEGER, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR, source_updated_at VARCHAR, value DOUBLE)")
    con.execute("INSERT INTO geography_registry VALUES ('es11','ESP','ES11','Galicia','NUTS_2024','nuts2')")
    con.execute("INSERT INTO subnational_observations VALUES ('NUTS_2024','ES11','nuts2','regional_unemployment_rate',2025,'percent','EUROSTAT','lfst_r_lfu3rt','2026-01-01',5.5)")
    con.close()
    before = path.stat().st_size
    report = build_report(path, "regional_unemployment_rate")
    assert report["observation_count"] == 1
    assert report["locations"][0]["source_geo_code"] == "ES11"
    assert report["locations"][0]["source_id"] == "EUROSTAT"
    assert "value" not in report["locations"][0]
    assert "not_vintage_certification" in report["status"]
    assert path.stat().st_size == before
