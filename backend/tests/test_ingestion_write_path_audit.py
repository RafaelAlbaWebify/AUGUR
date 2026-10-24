"""Structural regression gate for central evidence-write safety."""
from pathlib import Path
from scripts.audit_ingestion_write_paths import audit_source


def current_analytics():
    return (Path(__file__).resolve().parents[1]/"app/db/analytics.py").read_text()


def test_known_central_write_paths_pass_all_contracts():
    report=audit_source(current_analytics())
    assert report["status"]=="passed", report["issues"]
    assert report["protected_observation_writers"]==11
    assert report["writer_count"]==14


def test_new_writer_must_be_classified_and_reviewed():
    result=audit_source(current_analytics()+"\ndef upsert_unreviewed(rows):\n    pass\n")
    assert result["status"]=="failed"
    assert any("Unreviewed new write" in problem for problem in result["issues"])


def test_lost_transaction_guard_rejected():
    source=current_analytics()
    assert "con.execute('BEGIN TRANSACTION')" in source
    result=audit_source(source.replace("con.execute('BEGIN TRANSACTION')","con.execute('BEGIN')",1))
    assert result["status"]=="failed"
    assert any("missing explicit BEGIN TRANSACTION" in x for x in result["issues"])


def test_missing_batch_validation_rejected():
    source=current_analytics()
    assert "validate_write_batch(rows, subnational=False)" in source
    result=audit_source(source.replace("validate_write_batch(rows, subnational=False)",
                                       "list(rows)",1))
    assert result["status"]=="failed"
    assert any("missing batch validation" in x for x in result["issues"])


def test_validation_after_database_connection_is_rejected():
    source = current_analytics()
    old = "validate_write_batch(rows, subnational=True)"
    assert old in source
    mutated = source.replace(
        old, "duckdb.connect(str(settings.duckdb_path)).close()\n    " + old, 1
    )
    result = audit_source(mutated)
    assert result["status"] == "failed"
    assert any("upsert_subnational_observations: batch validation must precede database connection"
               in issue for issue in result["issues"])
    assert audit_source(source)["status"] == "passed"
