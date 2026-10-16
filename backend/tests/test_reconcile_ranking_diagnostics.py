"""Diagnostics distinguish provider extra dimensions from actual value deltas."""
import duckdb
from scripts.reconcile_ranking_eurostat import reconcile


class DiagnosticProvider:
    def fetch_dataset(self, dataset_id, filters):
        return {"dataset": dataset_id, "geo": filters["geo"]}

    def normalize(self, country, config, response):
        rows = []
        for geo in response["geo"]:
            base = {"geo": geo, "time": "2025", "freq": "A",
                    "age": "Y20-64", "sex": "T", "unit": "PC"}
            if response["dataset"] == "lfst_r_lfu3rt":
                for duration in ("TOTAL", "LT12"):
                    rows.append({"period": 2025, "value": 6.0,
                                 "source_dimensions": {**base, "isced11": "TOTAL", "duration": duration},
                                 "source_observation_status": None})
            else:
                rows.append({"period": 2025, "value": 8.0,
                             "source_dimensions": base,
                             "source_observation_status": None})
        return rows


def test_diagnostics_redact_values_and_preserve_read_only_db(tmp_path):
    path = tmp_path / "sample.duckdb"
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE geography_registry (country_iso3 VARCHAR, source_geo_code VARCHAR, geography_system VARCHAR, geo_level VARCHAR)")
    con.execute("CREATE TABLE subnational_observations (geo_code VARCHAR, geography_system VARCHAR, geo_level VARCHAR, indicator_id VARCHAR, period INTEGER, value DOUBLE, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR)")
    con.execute("INSERT INTO geography_registry VALUES ('ESP','ES11','NUTS_2024','nuts2')")
    for metric, dataset in (("regional_unemployment_rate", "lfst_r_lfu3rt"),
                            ("regional_employment_rate", "lfst_r_lfe2emprt")):
        con.execute("INSERT INTO subnational_observations VALUES ('ES11','NUTS_2024','nuts2',?,2025,6.0,'percent','EUROSTAT',?)", [metric, dataset])
    con.close()
    original_size = path.stat().st_size
    data = reconcile(path, DiagnosticProvider())
    unemp = data["metrics"]["regional_unemployment_rate"]
    assert unemp["duplicate_diagnostics"] == [{
        "geo_code": "ES11", "candidate_rows": 2,
        "distinct_dimension_tuples": 2, "extra_dimension_keys": ["duration", "isced11"]
    }]
    emp = data["metrics"]["regional_employment_rate"]
    assert emp["discrepancy_diagnostics"] == [{
        "geo_code": "ES11", "absolute_delta_percentage_points": 2.0
    }]
    assert "local_value" not in str(data)
    assert "provider_value" not in str(data)
    assert path.stat().st_size == original_size
