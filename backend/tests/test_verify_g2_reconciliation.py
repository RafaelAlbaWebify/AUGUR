from pathlib import Path

import duckdb

from scripts.verify_g2_reconciliation import validate


CODES = ("IE01", "IE02", "PT16", "PT17", "PT18")


def make_db(path: Path, reconciled: bool, unexpected: bool = False):
    con = duckdb.connect(str(path))
    try:
        con.execute("CREATE TABLE geography_registry(geo_id VARCHAR, geography_system VARCHAR, source_geo_code VARCHAR)")
        con.execute("CREATE TABLE subnational_observations(geography_system VARCHAR, geo_code VARCHAR, indicator_id VARCHAR, period INTEGER, value DOUBLE)")
        con.execute("CREATE TABLE metadata(key VARCHAR, value VARCHAR)")
        con.execute("INSERT INTO metadata VALUES ('status', ?)", ["bad" if unexpected else "ok"])
        for code in CODES:
            if not reconciled:
                con.execute("INSERT INTO geography_registry VALUES (?, 'NUTS_2024', ?)", [f"NUTS_2024:{code}",code])
            for i in range(172 // len(CODES) + (1 if CODES.index(code) < 172 % len(CODES) else 0)):
                con.execute("INSERT INTO subnational_observations VALUES (?, ?, ?, 2000, 70.0)",
                    ["NUTS_UNSPECIFIED" if reconciled else "NUTS_2024", code, f"indicator_{i}"])
        con.execute("INSERT INTO subnational_observations VALUES ('NUTS_2024','IE04','safe',2025,50)")
    finally:
        con.close()


def test_valid_exact_comparison(tmp_path):
    original, fixed = tmp_path / "original.duckdb", tmp_path / "fixed.duckdb"
    make_db(original, False)
    make_db(fixed, True)
    result = validate(original, fixed)
    assert result["passed"]
    assert result["observation_rows_relabelled"] == 172
    assert result["registry_rows_removed"] == 5


def test_unexpected_other_table_change_is_rejected(tmp_path):
    original, fixed = tmp_path / "original.duckdb", tmp_path / "fixed.duckdb"
    make_db(original, False)
    make_db(fixed, True, unexpected=True)
    result = validate(original, fixed)
    assert not result["passed"]
    assert "Unanticipated difference in table metadata" in result["failures"]


def test_unexpected_observation_change_is_rejected(tmp_path):
    original, fixed = tmp_path / "original.duckdb", tmp_path / "fixed.duckdb"
    make_db(original, False)
    make_db(fixed, True)
    con = duckdb.connect(str(fixed))
    con.execute("UPDATE subnational_observations SET value=9000 WHERE geo_code='IE04'")
    con.close()
    result = validate(original, fixed)
    assert not result["passed"]
    assert any("Observation content differs" in x for x in result["failures"])
