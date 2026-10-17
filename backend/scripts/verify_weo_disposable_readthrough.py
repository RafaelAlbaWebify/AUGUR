"""Independent CI-only storage round-trip for official IMF WEO observations."""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import duckdb
from app.db import analytics


def verify_weo_roundtrip(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("Cannot accept empty WEO reference")
    with TemporaryDirectory(prefix="augur-weo-reference-") as directory:
        path=Path(directory)/"weo.duckdb"
        con=duckdb.connect(str(path))
        try:
            con.execute("""CREATE TABLE observations (
              country_iso3 VARCHAR, indicator_id VARCHAR, period INTEGER,
              value DOUBLE, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR,
              observation_type VARCHAR, retrieved_at TIMESTAMP,
              source_updated_at VARCHAR, source_observation_status VARCHAR,
              source_decimal INTEGER,
              PRIMARY KEY(country_iso3, indicator_id, period, source_id))""")
        finally:
            con.close()
        old=analytics.settings
        analytics.settings=SimpleNamespace(duckdb_path=path)
        try:
            count=analytics.upsert_observations(rows)
        finally:
            analytics.settings=old
        con=duckdb.connect(str(path),read_only=True)
        try:
            values=con.execute("""SELECT country_iso3, indicator_id, period,
                         value, observation_type, dataset_id FROM observations""").fetchall()
        finally:
            con.close()
        expected={(r["country_iso3"],r["indicator_id"],r["period"],r["value"],
                   r["observation_type"],r["dataset_id"]) for r in rows}
        actual=set(values)
        if count!=len(rows) or len(actual)!=len(rows) or expected!=actual:
            raise ValueError("Official WEO source-to-DuckDB equality failed")
        return {"status":"source_to_disposable_duckdb_verified",
                "expected_rows":len(rows),"stored_rows":len(actual),
                "observed":sum(x[4]=="observed" for x in actual),
                "official_forecast":sum(x[4]=="official_forecast" for x in actual),
                "production_writes":0,"ranking_eligible":False}
