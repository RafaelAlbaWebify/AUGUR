"""Check age-cohort forensic report is deterministic, exact-filtered and read-only."""
import duckdb
from scripts.inspect_ranking_employment_age import inspect


class Provider:
    def fetch_dataset(self, dataset_id, filters):
        return {"dataset": dataset_id, "filters": filters}

    def normalize(self, geo, config, payload):
        assert config["dimension_values"] == payload["filters"]
        age = payload["filters"]["age"]
        return [{"period": 2025, "value": 65.0 if age == "Y15-64" else 71.0,
                 "source_dimensions": {"geo": geo, "time": "2025",
                                       "age": age, "sex": "T", "freq": "A", "unit": "PC"},
                 "source_observation_status": None}]


def test_local_historical_record_matches_only_15_64(tmp_path):
    db = tmp_path / "fixture.duckdb"
    con = duckdb.connect(str(db))
    con.execute("""CREATE TABLE subnational_observations (
       geo_code VARCHAR, geography_system VARCHAR, indicator_id VARCHAR,
       period INTEGER, value DOUBLE, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR
    )""")
    con.execute("""INSERT INTO subnational_observations VALUES (
       'ES11','NUTS_2024','regional_employment_rate',2025,65.0,'percent',
       'EUROSTAT','lfst_r_lfe2emprt')""")
    con.close()
    before = db.stat().st_size
    report = inspect(db, Provider(), codes=("ES11",))
    pair = report["records"][0]["age_cohorts"]
    assert pair[0]["age"] == "Y15-64"
    assert pair[0]["within_tolerance"] is True
    assert pair[1]["age"] == "Y20-64"
    assert pair[1]["within_tolerance"] is False
    assert pair[1]["signed_delta_local_minus_provider"] == -6.0
    assert db.stat().st_size == before
