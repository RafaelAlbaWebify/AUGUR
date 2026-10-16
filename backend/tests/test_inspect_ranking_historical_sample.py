import duckdb
from scripts.inspect_ranking_historical_sample import inspect


class Source:
    def fetch_dataset(self, dataset_id, filters):
        return {"dataset": dataset_id, "filters": filters}
    def normalize(self, geo, config, payload):
        dimensions = {**payload["filters"]}
        return [{"period": 2025, "value": 5.0,
                 "source_dimensions": dimensions, "source_observation_status": None}]


def test_sample_never_changes_database(tmp_path):
    path = tmp_path / "sample.duckdb"
    con = duckdb.connect(str(path))
    con.execute("""CREATE TABLE subnational_observations (
        geo_code VARCHAR, indicator_id VARCHAR, period INTEGER, geography_system VARCHAR,
        value DOUBLE, source_id VARCHAR, dataset_id VARCHAR)""")
    con.execute("""INSERT INTO subnational_observations VALUES
        ('ES11','regional_unemployment_rate',2025,'NUTS_2024',6.0,'EUROSTAT','lfst_r_lfu3rt')""")
    con.close()
    size = path.stat().st_size
    report = inspect(path, Source(), codes=("ES11",))
    row = next(item for item in report["records"]
               if item["indicator_id"] == "regional_unemployment_rate")
    assert row["status"] == "paired_unverified"
    assert row["local_value"] == 6.0
    assert row["provider_value"] == 5.0
    assert row["signed_delta_local_minus_provider"] == 1.0
    assert row["local_response_dimensions"] is None
    assert path.stat().st_size == size
