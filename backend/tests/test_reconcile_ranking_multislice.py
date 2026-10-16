"""A multi-slice provider response must not be mistaken for duplicates."""
import duckdb
from scripts.reconcile_ranking_eurostat import reconcile


class MultiSliceProvider:
    def fetch_dataset(self, dataset_id, filters):
        return {"geo": filters["geo"]}

    def normalize(self, country, config, response):
        rows = []
        for geo in response["geo"]:
            for age, value in (("Y15-64", 88.0), ("Y20-64", 6.0)):
                rows.append({
                    "period": 2025, "value": value,
                    "source_dimensions": {
                        "geo": geo, "time": "2025", "age": age,
                        "freq": "A", "sex": "T", "unit": "PC",
                    },
                    "source_observation_status": None,
                })
        return rows


def test_irrelevant_provider_age_slices_do_not_create_duplicates(tmp_path):
    db = tmp_path / "test.duckdb"
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE geography_registry (country_iso3 VARCHAR, source_geo_code VARCHAR, geography_system VARCHAR, geo_level VARCHAR)")
    con.execute("CREATE TABLE subnational_observations (geo_code VARCHAR, geography_system VARCHAR, geo_level VARCHAR, indicator_id VARCHAR, period INTEGER, value DOUBLE, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR)")
    con.execute("INSERT INTO geography_registry VALUES ('ESP', 'ES11', 'NUTS_2024', 'nuts2')")
    for indicator, dataset in (
        ("regional_unemployment_rate", "lfst_r_lfu3rt"),
        ("regional_employment_rate", "lfst_r_lfe2emprt"),
    ):
        con.execute("INSERT INTO subnational_observations VALUES ('ES11', 'NUTS_2024', 'nuts2', ?, 2025, 6.0, 'percent', 'EUROSTAT', ?)", [indicator, dataset])
    con.close()
    size = db.stat().st_size
    result = reconcile(db, MultiSliceProvider())
    for outcome in result["metrics"].values():
        assert outcome["value_matches_within_tolerance"] == 1
        assert outcome["issues"] == []
    assert db.stat().st_size == size
