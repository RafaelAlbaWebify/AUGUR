"""Bulk national ingestion retains exact data, rollback, and bounded write staging."""
from datetime import datetime, timezone
from types import SimpleNamespace

import duckdb
import pytest
from app.db import analytics


COLUMNS = """country_iso3 VARCHAR NOT NULL, indicator_id VARCHAR NOT NULL,
period INTEGER NOT NULL, value DOUBLE NOT NULL CHECK(value < 100),
unit VARCHAR, source_id VARCHAR NOT NULL, dataset_id VARCHAR NOT NULL,
observation_type VARCHAR NOT NULL, retrieved_at TIMESTAMP NOT NULL,
source_updated_at VARCHAR, source_observation_status VARCHAR, source_decimal INTEGER,
PRIMARY KEY(country_iso3, indicator_id, period, source_id)"""


def connect_fixture(tmp_path, monkeypatch):
    path = tmp_path / "bulk.duckdb"
    con = duckdb.connect(str(path))
    con.execute(f"CREATE TABLE observations ({COLUMNS})")
    con.close()
    monkeypatch.setattr(analytics, "settings", SimpleNamespace(duckdb_path=path))
    return path


def rows(n):
    stamp=datetime(2026,10,17,tzinfo=timezone.utc)
    return [{"country_iso3":"ESP","indicator_id":"series", "period":2000+i,
             "value":float(i % 90), "unit":None if i%3==0 else "percent",
             "source_id":"TEST","dataset_id":"test_source",
             "observation_type":"observed","retrieved_at":stamp,
             "source_updated_at":None if i%2==0 else "2026-10-17",
             "source_observation_status":"d" if i%7==0 else None,
             "source_decimal":None if i%5==0 else 1} for i in range(n)]


def test_bulk_preserves_values_nulls_flags_and_replaces_exact_keys(tmp_path,monkeypatch):
    path=connect_fixture(tmp_path,monkeypatch)
    data=rows(120)
    assert analytics.upsert_observations(data)==120
    con=duckdb.connect(str(path),read_only=True)
    try:
        assert con.execute("SELECT COUNT(*) FROM observations").fetchone()[0]==120
        assert con.execute("SELECT unit, source_updated_at, source_observation_status, source_decimal FROM observations WHERE period=2000").fetchone()==(None,None,"d",None)
    finally:con.close()
    changed=dict(data[0],value=42.0)
    assert analytics.upsert_observations([changed])==1
    con=duckdb.connect(str(path),read_only=True)
    try:
        assert con.execute("SELECT COUNT(*), MAX(value) FROM observations WHERE period=2000").fetchone()==(1,42.0)
    finally:con.close()


def test_bulk_rejects_later_sql_failure_atomically(tmp_path,monkeypatch):
    path=connect_fixture(tmp_path,monkeypatch)
    assert analytics.upsert_observations(rows(12))==12
    changed=[dict(x,value=50.0) for x in rows(12)]
    changed[-1]["value"]=100.5
    with pytest.raises(Exception):
        analytics.upsert_observations(changed)
    con=duckdb.connect(str(path),read_only=True)
    try:
        assert con.execute("SELECT value FROM observations WHERE period=2000").fetchone()[0]==0.0
        assert con.execute("SELECT COUNT(*) FROM observations").fetchone()[0]==12
    finally:con.close()


def test_bulk_larger_batch_without_per_row_primary_key_replace(tmp_path,monkeypatch):
    path=connect_fixture(tmp_path,monkeypatch)
    data=rows(5000)
    assert analytics.upsert_observations(data)==5000
    con=duckdb.connect(str(path),read_only=True)
    try:
        assert con.execute("SELECT COUNT(*) FROM observations").fetchone()[0]==5000
    finally:con.close()
