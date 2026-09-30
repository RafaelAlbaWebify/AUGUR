import sqlite3
from pathlib import Path

import duckdb

from app.core.config import settings


def initialize_sqlite(path: Path) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        con.execute(
            """
            INSERT OR REPLACE INTO app_metadata(key, value)
            VALUES ('schema_version', 'phase0')
            """
        )
        con.commit()
    finally:
        con.close()


def initialize_duckdb(path: Path) -> None:
    con = duckdb.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_metadata (
                key VARCHAR PRIMARY KEY,
                value VARCHAR NOT NULL
            )
            """
        )
        con.execute(
            """
            INSERT OR REPLACE INTO analytics_metadata
            VALUES ('schema_version', 'phase0')
            """
        )
    finally:
        con.close()


def initialize_datastores() -> None:
    initialize_sqlite(settings.sqlite_path)
    initialize_duckdb(settings.duckdb_path)


def datastore_status() -> dict[str, bool]:
    result = {"sqlite": False, "duckdb": False}

    try:
        con = sqlite3.connect(settings.sqlite_path)
        try:
            value = con.execute(
                "SELECT value FROM app_metadata WHERE key='schema_version'"
            ).fetchone()
            result["sqlite"] = value is not None
        finally:
            con.close()
    except Exception:
        pass

    try:
        con = duckdb.connect(str(settings.duckdb_path), read_only=True)
        try:
            value = con.execute(
                "SELECT value FROM analytics_metadata WHERE key='schema_version'"
            ).fetchone()
            result["duckdb"] = value is not None
        finally:
            con.close()
    except Exception:
        pass

    return result
