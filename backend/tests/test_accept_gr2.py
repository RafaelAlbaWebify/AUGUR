"""Acceptance runner is fail-closed and does not alter the local database."""
import duckdb
from scripts.accept_gr2 import accept, database_evidence


class Provider:
    def fetch_dataset(self, dataset_id, filters):
        return {"filters": filters, "dataset": dataset_id}

    def normalize(self, country, config, payload):
        rows = []
        for geo in ([payload["filters"]["geo"]] if isinstance(payload["filters"]["geo"], str)
                    else payload["filters"]["geo"]):
            dimensions = dict(payload["filters"], geo=geo)
            rows.append({"period": 2025, "value": 7.0,
                         "source_dimensions": dimensions,
                         "source_observation_status": None})
        return rows


def test_accept_gr2_report_does_not_write_duckdb(tmp_path):
    db = tmp_path / "local.duckdb"
    con = duckdb.connect(str(db))
    con.execute("""CREATE TABLE subnational_observations (
        geography_system VARCHAR, geo_code VARCHAR, geo_level VARCHAR,
        indicator_id VARCHAR, period INTEGER, value DOUBLE, unit VARCHAR,
        source_id VARCHAR, dataset_id VARCHAR)""")
    con.execute("""CREATE TABLE geography_registry (
        geography_system VARCHAR, source_geo_code VARCHAR, geo_level VARCHAR,
        country_iso3 VARCHAR)""")
    con.execute("INSERT INTO geography_registry VALUES ('NUTS_2024','ES11','nuts2','ESP')")
    con.execute("""INSERT INTO subnational_observations VALUES
        ('NUTS_2024','ES11','nuts2','regional_employment_rate',2025,6,'percent','EUROSTAT','lfst_r_lfe2emprt'),
        ('NUTS_2024','ES11','nuts2','regional_unemployment_rate',2025,6,'percent','EUROSTAT','lfst_r_lfu3rt')""")
    con.close()
    original = database_evidence(db)
    result = accept(db, Provider())
    assert result["database_unchanged"] is True
    assert result["status"] == "diagnostic_complete_not_certified"
    assert result["database"]["pilot_rows"]["regional_employment_rate"]["records"] == 1
    assert result["acceptance_gates"]["numerical_rankings"] == "blocked"
    assert database_evidence(db)["sha256"] == original["sha256"]
