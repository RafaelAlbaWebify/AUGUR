"""Three reviewed revisions: fail-closed source evidence and atomic apply."""
from pathlib import Path
import duckdb
import pytest
from scripts.apply_compare_revisions import ALLOWED, prepare, apply


def report():
    vals = {
        "ESP": {"before": 100.7, "after": 100.5},
        "IRL": {"before": 32.9, "after": 34.8},
    }
    rows = []
    for country, indicator, year, source, dataset in sorted(ALLOWED):
        before, after = ((2.699932857627, 2.67326741144651)
                         if indicator == "inflation_cpi" else
                         (vals[country]["before"], vals[country]["after"]))
        rows.append({"country": country, "indicator_id": indicator, "period": year,
                     "provider": source, "stored_dataset": dataset, "status": "value_drift",
                     "stored_value": before, "current_value": after,
                     "source_updated_at": "2026-10-21"})
    return {"scope": "read_only_provider_reconciliation", "rows": len(rows),
            "results": rows}


def make_db(path, revisions):
    con = duckdb.connect(str(path))
    try:
        con.execute("""CREATE TABLE observations(
            country_iso3 VARCHAR, indicator_id VARCHAR, period INTEGER, source_id VARCHAR,
            dataset_id VARCHAR, observation_type VARCHAR, value DOUBLE, unit VARCHAR,
            retrieved_at TIMESTAMP, source_updated_at VARCHAR,
            source_observation_status VARCHAR, source_decimal INTEGER)""")
        for item in revisions:
            country, indicator, period, source, dataset = item["key"]
            con.execute("INSERT INTO observations VALUES (?,?,?,?,?,'observed',?,'percent',CURRENT_TIMESTAMP,'previous',NULL,NULL)",
                        [country, indicator, period, source, dataset, item["before"]])
    finally:
        con.close()


def test_three_revisions_are_required_not_a_subset():
    batch = report()
    assert len(prepare(batch)) == 3
    batch["results"].pop()
    batch["rows"] = 2
    with pytest.raises(ValueError, match="all three"):
        prepare(batch)


def test_unreviewed_change_rejected():
    batch = report()
    batch["results"][0]["indicator_id"] = "population_total"
    with pytest.raises(ValueError, match="Unapproved"):
        prepare(batch)


def test_dry_run_writes_backup_but_not_db(tmp_path):
    revisions = prepare(report())
    db = tmp_path / "sandbox.duckdb"
    make_db(db, revisions)
    backup = tmp_path / "preflight.json"
    result = apply(db, revisions, backup, commit=False)
    assert result["status"] == "preflight_snapshot"
    assert backup.exists()
    con = duckdb.connect(str(db), read_only=True)
    try:
        assert sorted(x[0] for x in con.execute("SELECT value FROM observations").fetchall()) == sorted(
            item["before"] for item in revisions)
    finally:
        con.close()


def test_apply_exactly_three_revisions_and_preserve_audit(tmp_path):
    revisions = prepare(report())
    db = tmp_path / "sandbox.duckdb"
    make_db(db, revisions)
    backup = tmp_path / "snapshot.json"
    assert apply(db, revisions, backup, commit=True)["status"] == "applied"
    import json
    assert len(json.loads(backup.read_text())["changes"]) == 3
    con = duckdb.connect(str(db), read_only=True)
    try:
        for item in revisions:
            assert con.execute("SELECT value FROM observations WHERE country_iso3=? AND indicator_id=?",
                               [item["key"][0], item["key"][1]]).fetchone()[0] == item["after"]
    finally:
        con.close()


def test_changed_operator_data_blocks_all_writes(tmp_path):
    revisions = prepare(report())
    db = tmp_path / "sandbox.duckdb"
    make_db(db, revisions)
    con = duckdb.connect(str(db))
    con.execute("UPDATE observations SET value=999 WHERE country_iso3='ESP' AND indicator_id='public_debt_gdp'")
    con.close()
    with pytest.raises(ValueError, match="changed since audit"):
        apply(db, revisions, tmp_path / "do_not_write.json", commit=True)
    assert not (tmp_path / "do_not_write.json").exists()
