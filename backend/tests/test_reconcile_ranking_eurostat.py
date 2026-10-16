import duckdb
from scripts.reconcile_ranking_eurostat import reconcile


class FakeEurostat:
    def fetch_dataset(self, dataset_id, filters):
        return {"dataset": dataset_id, "filters": filters}

    def normalize(self, country, config, payload):
        return [
            {"period": 2025, "value": 6.0,
             "source_dimensions": {"geo": code, "freq": "A", "age": "Y20-64",
                                   "sex": "T", "unit": "PC", "time": "2025",
                                   **({"isced11": "TOTAL"} if payload["dataset"] == "lfst_r_lfu3rt" else {})},
             "source_observation_status": None}
            for code in payload["filters"]["geo"]
        ]


def test_reconcile_reports_mismatch_and_preserves_local_db(tmp_path):
    db = tmp_path / "test.duckdb"
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE geography_registry (country_iso3 VARCHAR, source_geo_code VARCHAR, geography_system VARCHAR, geo_level VARCHAR)")
    con.execute("CREATE TABLE subnational_observations (geo_code VARCHAR, geography_system VARCHAR, geo_level VARCHAR, indicator_id VARCHAR, period INTEGER, value DOUBLE, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR)")
    con.execute("INSERT INTO geography_registry VALUES ('ESP', 'ES11', 'NUTS_2024', 'nuts2')")
    con.execute("INSERT INTO subnational_observations VALUES ('ES11', 'NUTS_2024', 'nuts2', 'regional_unemployment_rate', 2025, 6.0, 'percent', 'EUROSTAT', 'lfst_r_lfu3rt')")
    con.execute("INSERT INTO subnational_observations VALUES ('ES11', 'NUTS_2024', 'nuts2', 'regional_employment_rate', 2025, 7.0, 'percent', 'EUROSTAT', 'lfst_r_lfe2emprt')")
    con.close()
    before = db.stat().st_size
    report = reconcile(db, FakeEurostat())
    assert report["metrics"]["regional_unemployment_rate"]["value_matches_within_tolerance"] == 1
    assert report["metrics"]["regional_employment_rate"]["issues"] == [
        {"geo_code": "ES11", "country_iso3": "ESP", "reason": "value_discrepancy"}
    ]
    assert "value" not in report["metrics"]["regional_employment_rate"]["issues"][0]
    assert db.stat().st_size == before
