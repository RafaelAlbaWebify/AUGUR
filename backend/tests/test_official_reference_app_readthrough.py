"""Reference-to-application roundtrip: DB/service/real HTTP, with no local operator database."""
import json
from datetime import datetime, timezone
import duckdb
import pytest
from scripts.build_official_reference_db import CODES, INDICATORS, PERIOD
from scripts.verify_reference_app_readthrough import verify
from app.services.regional_evidence import REGIONAL_INDICATORS


def create_reference(path, *, duplicate=False):
    cfg={r["indicator_id"]:r for r in REGIONAL_INDICATORS}
    con=duckdb.connect(str(path))
    con.execute("""CREATE TABLE reference_observations(
      country_iso3 VARCHAR,geo_code VARCHAR,indicator_id VARCHAR,period INTEGER,
      value DOUBLE,unit VARCHAR,source_id VARCHAR,dataset_id VARCHAR,
      source_dimensions_json VARCHAR,source_status VARCHAR,
      source_updated_at VARCHAR,retrieved_at VARCHAR)""")
    rows=[]
    for country,codes in CODES.items():
        for geo in codes:
            for indicator in INDICATORS:
                spec=cfg[indicator]
                dims={**spec["filters"],"geo":geo,"time":str(PERIOD)}
                rows.append((country,geo,indicator,PERIOD,5.0,spec["unit"],"EUROSTAT",
                    spec["dataset_id"],json.dumps(dims), "d" if country=="ESP" else None,
                    "2026-10-17",datetime.now(timezone.utc).isoformat()))
    if duplicate:
        rows[-1]=rows[0]
    con.executemany("INSERT INTO reference_observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",rows)
    con.close()


def test_official_reference_reaches_app_storage_and_http_with_no_vintage_release(tmp_path):
    path=tmp_path/"reference.duckdb"
    create_reference(path)
    result=verify(path)
    assert result["source_rows"]==result["app_rows"]==62
    assert result["service_geographies"]==31
    assert result["ranking_api_exposed_items"]==0
    assert result["ranking_api_status"]=="blocked_unverified_evidence"
    assert result["registered_geographies"]==0
    assert result["source_flag_counts"]["d"]==38
    assert result["production_writes"]==0


def test_duplicate_official_ref_cannot_replace_an_app_observation(tmp_path):
    path=tmp_path/"bad_reference.duckdb"
    create_reference(path,duplicate=True)
    with pytest.raises(ValueError, match="Duplicate observation write key"):
        verify(path)
