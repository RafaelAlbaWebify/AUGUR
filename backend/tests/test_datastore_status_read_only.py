"""A datastore health check must never create a missing SQLite file."""
import sqlite3
from types import SimpleNamespace
from app.db import bootstrap


def test_missing_sqlite_is_not_created_by_health_check(tmp_path,monkeypatch):
    sqlite_path=tmp_path/"absent"/"operator.sqlite"
    duckdb_path=tmp_path/"absent"/"operator.duckdb"
    monkeypatch.setattr(bootstrap,"settings",SimpleNamespace(
        sqlite_path=sqlite_path,duckdb_path=duckdb_path))
    assert bootstrap.datastore_status()=={"sqlite":False,"duckdb":False}
    assert not sqlite_path.exists()
    assert not duckdb_path.exists()
    assert not sqlite_path.parent.exists()


def test_health_check_reads_existing_sqlite_schema(tmp_path,monkeypatch):
    path=tmp_path/"app.sqlite"
    con=sqlite3.connect(path)
    try:
        con.execute("CREATE TABLE app_metadata(key TEXT,value TEXT)")
        con.execute("INSERT INTO app_metadata VALUES('schema_version','phase1')")
        con.commit()
    finally:
        con.close()
    monkeypatch.setattr(bootstrap,"settings",SimpleNamespace(
        sqlite_path=path,duckdb_path=tmp_path/"missing.duckdb"))
    result=bootstrap.datastore_status()
    assert result["sqlite"] is True
    assert result["duckdb"] is False
