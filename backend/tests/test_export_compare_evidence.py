"""Disposable DuckDB evidence export regression; never reads operator data."""
import duckdb
from scripts.export_compare_evidence import collect


def test_export_matches_compare_source_priority_and_observed_boundary(tmp_path):
    path = tmp_path / "evidence.duckdb"
    con = duckdb.connect(str(path))
    try:
        con.execute("CREATE TABLE indicators(indicator_id VARCHAR, name VARCHAR, dimension VARCHAR)")
        con.execute("INSERT INTO indicators VALUES ('employment','Employment','productive_capacity')")
        con.execute("CREATE TABLE sources(source_id VARCHAR, priority INTEGER)")
        con.execute("INSERT INTO sources VALUES ('EUROSTAT',1),('OTHER',2)")
        con.execute("""CREATE TABLE observations(
            country_iso3 VARCHAR, indicator_id VARCHAR, period INTEGER,
            value DOUBLE, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR,
            observation_type VARCHAR, retrieved_at TIMESTAMP, source_updated_at VARCHAR,
            source_observation_status VARCHAR, source_decimal INTEGER)""")
        con.execute("""INSERT INTO observations VALUES
            ('ESP','employment',2025,72.4,'percent','EUROSTAT','lfsi_emp_a',
             'observed','2026-10-01', '2026-09-01',NULL,1),
            ('ESP','employment',2025,73.1,'percent','OTHER','alternate',
             'observed','2026-10-02',NULL,NULL,1),
            ('ESP','employment',2026,99.0,'percent','EUROSTAT','future',
             'official_forecast','2026-10-02',NULL,NULL,1),
            ('IRL','employment',2025,80.2,'percent','EUROSTAT','lfsi_emp_a',
             'observed','2026-10-01',NULL,NULL,1)""")
    finally:
        con.close()
    result = collect(path)
    assert result["read_only"] is True
    assert result["country_counts"] == {"ESP": 1, "IRL": 1}
    rows = {item["country_iso3"]: item for item in result["rows"]}
    assert rows["ESP"]["value"] == 72.4
    assert rows["ESP"]["dataset_id"] == "lfsi_emp_a"
    assert rows["ESP"]["period"] == 2025
    assert rows["IRL"]["value"] == 80.2
    assert rows["ESP"]["retrieved_at"].startswith("2026-10-01")
    check = duckdb.connect(str(path), read_only=True)
    try:
        assert check.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 4
    finally:
        check.close()
