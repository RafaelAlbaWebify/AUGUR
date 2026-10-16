import duckdb
from scripts.inspect_ranking_employment_age import registered_pilot_codes, summarize


def test_registered_codes_scope_is_2025_pilot_only(tmp_path):
    db = tmp_path / "sample.duckdb"
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE geography_registry (country_iso3 VARCHAR, source_geo_code VARCHAR, geography_system VARCHAR, geo_level VARCHAR)")
    con.execute("CREATE TABLE subnational_observations (geo_code VARCHAR, geography_system VARCHAR, geo_level VARCHAR, indicator_id VARCHAR, period INTEGER)")
    con.execute("INSERT INTO geography_registry VALUES ('ESP','ES11','NUTS_2024','nuts2'),('PRT','PT11','NUTS_2024','nuts2'),('FRA','FR10','NUTS_2024','nuts2')")
    con.execute("INSERT INTO subnational_observations VALUES ('ES11','NUTS_2024','nuts2','regional_employment_rate',2025),('PT11','NUTS_2024','nuts2','regional_employment_rate',2025),('FR10','NUTS_2024','nuts2','regional_employment_rate',2025),('ES11','NUTS_2024','nuts2','regional_employment_rate',2024)")
    con.close()
    before = db.stat().st_size
    assert registered_pilot_codes(db) == ("ES11", "PT11")
    assert db.stat().st_size == before


def test_summary_does_not_count_unresolved_as_matches():
    assert summarize({"records": [
        {"status": "diagnostic_only", "age_cohorts": [
            {"age":"Y15-64","status":"paired_unverified","within_tolerance":True},
            {"age":"Y20-64","status":"paired_unverified","within_tolerance":False},
        ]},
        {"status":"provider_error"},
    ]}) == {"total":2, "matches_15_64":1, "matches_20_64":0, "unresolved":1}
