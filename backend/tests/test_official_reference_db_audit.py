"""Regression tests for independently auditing persisted official-source reference data."""
import json
from pathlib import Path
import duckdb
import pytest
from scripts.audit_official_reference_db import audit
from scripts.build_official_reference_db import CODES, INDICATORS, PERIOD
from app.services.regional_evidence import REGIONAL_INDICATORS


@pytest.fixture
def reference(tmp_path):
    db = tmp_path / "reference.duckdb"
    config = {r["indicator_id"]: r for r in REGIONAL_INDICATORS}
    con = duckdb.connect(str(db))
    con.execute("""CREATE TABLE reference_observations (
      country_iso3 VARCHAR, geo_code VARCHAR, indicator_id VARCHAR, period INTEGER,
      value DOUBLE, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR,
      source_dimensions_json VARCHAR, source_status VARCHAR, source_updated_at VARCHAR,
      retrieved_at VARCHAR)""")
    for country, codes in CODES.items():
        for code in codes:
            for indicator in INDICATORS:
                contract = config[indicator]
                dims = {**contract["filters"], "geo": code, "time": str(PERIOD)}
                con.execute("INSERT INTO reference_observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
                    country, code, indicator, PERIOD, 70.0, contract["unit"], "EUROSTAT",
                    contract["dataset_id"], json.dumps(dims), None, None, "test",
                ])
    con.close()
    return db


def modify(db, sql, params=[]):
    con = duckdb.connect(str(db))
    try:
        con.execute(sql, params)
    finally:
        con.close()


def test_reference_passes_with_exact_contract(reference):
    result = audit(reference)
    assert result["status"] == "passed_not_quality_or_vintage_certified"
    assert result["rows"] == 62
    assert result["quality_certified"] is False


@pytest.mark.parametrize("statement,reason", [
    ("UPDATE reference_observations SET source_id='OTHER' WHERE geo_code='ES11'", "source_contract"),
    ("UPDATE reference_observations SET value='NaN' WHERE geo_code='ES11'", "invalid_value"),
    ("UPDATE reference_observations SET source_dimensions_json='{}' WHERE geo_code='ES11'", "dimension_mismatch"),
    ("DELETE FROM reference_observations WHERE geo_code='ES11'", "missing"),
])
def test_corruption_is_rejected(reference, statement, reason):
    modify(reference, statement)
    assert any(reason in error for error in audit(reference)["errors"])


def test_quality_status_is_reported_without_false_certification(reference):
    modify(reference, "UPDATE reference_observations SET source_status='d' WHERE geo_code='ES11'")
    result = audit(reference)
    assert result["flag_counts"]["regional_employment_rate:d"] == 1
    assert result["flag_counts"]["regional_unemployment_rate:d"] == 1
    assert result["quality_certified"] is False
