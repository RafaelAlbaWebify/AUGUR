"""Real DuckDB integration gates: atomic rollback and DB-to-ranking API equality.

Uses only disposable per-test databases. Never touches the operator's database.
"""
from datetime import datetime, timezone
from types import SimpleNamespace

import duckdb
import pytest

from app.db import analytics
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes import router
from app.services.regional_rankings import regional_rankings


def make_db(path):
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE countries (iso2 VARCHAR, iso3 VARCHAR)")
    con.execute("INSERT INTO countries VALUES ('ES','ESP')")
    con.execute("""CREATE TABLE geography_registry (
      geo_id VARCHAR PRIMARY KEY, country_iso3 VARCHAR, country_iso2 VARCHAR,
      name VARCHAR, geo_level VARCHAR, geography_system VARCHAR, source_id VARCHAR,
      source_geo_code VARCHAR, parent_geo_id VARCHAR, latitude DOUBLE, longitude DOUBLE)""")
    con.execute("""CREATE TABLE subnational_observations (
      geography_system VARCHAR, geo_code VARCHAR, geo_name VARCHAR, geo_level VARCHAR,
      indicator_id VARCHAR, period INTEGER, value DOUBLE CHECK(value < 50),
      unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR, retrieved_at TIMESTAMP,
      source_updated_at VARCHAR, request_filters_json VARCHAR, response_dimensions_json VARCHAR,
      source_observation_status VARCHAR,
      PRIMARY KEY(geography_system,geo_code,indicator_id,period,source_id))""")
    con.close()


def sample(value=7.1, name="Galicia"):
    import json
    return {
      "geo_code":"ES11", "geo_name":name, "geo_level":"NUTS2",
      "geography_system":"NUTS_2024", "country_iso3":"ESP",
      "indicator_id":"regional_unemployment_rate", "period":2025,
      "value":value, "unit":"percent", "source_id":"EUROSTAT",
      "dataset_id":"lfst_r_lfu3rt", "retrieved_at":datetime.now(timezone.utc),
      "response_dimensions_json":json.dumps({"geo":"ES11","time":"2025","freq":"A",
                 "age":"Y20-64","sex":"T","unit":"PC","isced11":"TOTAL"})
    }


def test_failed_upsert_rolls_back_geography_and_observation(tmp_path, monkeypatch):
    path=tmp_path/"rollback.duckdb"
    make_db(path)
    monkeypatch.setattr(analytics, "settings", SimpleNamespace(duckdb_path=path))
    assert analytics.upsert_subnational_observations([sample()]) == 1
    con=duckdb.connect(str(path),read_only=True)
    before_registry=con.execute("SELECT * FROM geography_registry").fetchall()
    before_observations=con.execute("SELECT * FROM subnational_observations").fetchall()
    con.close()
    with pytest.raises(Exception):
        analytics.upsert_subnational_observations([sample(value=99.0,name="Corrupted region")])
    con=duckdb.connect(str(path),read_only=True)
    try:
        assert con.execute("SELECT * FROM geography_registry").fetchall()==before_registry
        assert con.execute("SELECT * FROM subnational_observations").fetchall()==before_observations
    finally:
        con.close()


def test_stored_observation_matches_read_only_ranking_service_and_api(tmp_path, monkeypatch):
    path=tmp_path/"api.duckdb"
    make_db(path)
    monkeypatch.setattr(analytics, "settings", SimpleNamespace(duckdb_path=path))
    assert analytics.upsert_subnational_observations([sample(value=7.1)])==1
    from app.services import regional_rankings as ranking_module
    monkeypatch.setattr(ranking_module, "settings", SimpleNamespace(duckdb_path=path))
    test_app=FastAPI()
    test_app.include_router(router,prefix="/api")
    response=TestClient(test_app).get("/api/rankings/regions",params={"indicator_id":"regional_unemployment_rate", "countries":"ESP", "limit":10})
    assert response.status_code==200
    blocked=response.json()
    assert blocked["status"]=="blocked_unverified_evidence"
    assert blocked["items"]==[]
    eligible=regional_rankings("regional_unemployment_rate",countries=("ESP",),
                               db_path=path,verified_geo_ids=frozenset({"NUTS_2024:ES11"}))
    con=duckdb.connect(str(path),read_only=True)
    try:
        stored=con.execute("SELECT value FROM subnational_observations WHERE geo_code='ES11'").fetchone()[0]
    finally:
        con.close()
    assert eligible["eligible_total"]==1
    assert eligible["items"][0]["value"]==stored==7.1


def test_invalid_later_batch_row_changes_nothing(tmp_path,monkeypatch):
    path=tmp_path/"reject.duckdb"
    make_db(path)
    monkeypatch.setattr(analytics,"settings",SimpleNamespace(duckdb_path=path))
    with pytest.raises(ValueError,match="Invalid observation value"):
        analytics.upsert_subnational_observations([sample(),sample(value=float("nan"),name="bad")])
    con=duckdb.connect(str(path),read_only=True)
    try:
        assert con.execute("SELECT COUNT(*) FROM geography_registry").fetchone()[0]==0
        assert con.execute("SELECT COUNT(*) FROM subnational_observations").fetchone()[0]==0
    finally:
        con.close()
