from types import SimpleNamespace
import duckdb
from app.services import observation_provenance as module


def test_source_unit_periods_not_silently_combined(tmp_path, monkeypatch):
    path = tmp_path / "audit.duckdb"
    con = duckdb.connect(str(path))
    con.execute("""CREATE TABLE geography_registry (
        geo_id VARCHAR, country_iso3 VARCHAR, geography_system VARCHAR,
        geo_level VARCHAR, source_geo_code VARCHAR
    )""")
    con.execute("""CREATE TABLE subnational_observations (
        geography_system VARCHAR, geo_level VARCHAR, geo_code VARCHAR,
        indicator_id VARCHAR, source_id VARCHAR, dataset_id VARCHAR,
        unit VARCHAR, period INTEGER, retrieved_at TIMESTAMP
    )""")
    con.execute("INSERT INTO geography_registry VALUES ('g1','ESP','NUTS_2024','nuts2','ES11')")
    con.executemany("INSERT INTO subnational_observations VALUES (?,?,?,?,?,?,?,?,?)", [
        ("NUTS_2024","nuts2","ES11","income","A","D1","EUR",2023,"2026-10-01"),
        ("NUTS_2024","nuts2","ES11","income","A","D1","EUR",2024,"2026-10-02"),
        ("NUTS_2024","nuts2","ES11","income","B","D2","PPS",2024,"2026-10-03"),
        ("NUTS_2024","nuts2","ES99","income","A","D1","EUR",2024,"2026-10-04"),
    ])
    con.close()
    monkeypatch.setattr(module, "settings", SimpleNamespace(duckdb_path=path))
    output = module.observation_provenance("esp")
    assert output["row_count"] == 2
    assert [(row["source_id"], row["unit"], row["observation_rows"])
            for row in output["items"]] == [("A", "EUR", 2), ("B", "PPS", 1)]
    assert output["items"][0]["distinct_periods"] == 2
    assert output["items"][1]["distinct_periods"] == 1
    assert output["unregistered_observations"][0]["geo_code"] == "ES99"
