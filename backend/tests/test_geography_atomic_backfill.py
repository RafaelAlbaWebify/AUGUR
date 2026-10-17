"""B02 geography writes are atomic and schema bootstrap cannot erase enrichment."""
from datetime import datetime, timezone
from types import SimpleNamespace
import duckdb
import pytest
from app.db import analytics


@pytest.fixture
def isolated_db(tmp_path,monkeypatch):
    path=tmp_path/"geo-test.duckdb"
    monkeypatch.setattr(analytics,"settings",SimpleNamespace(duckdb_path=path))
    analytics.initialize_analytics_schema()
    return path


def geography(code,**kw):
    return {"geo_id":"OECD_FUA:"+code,"country_iso3":"ESP","country_iso2":"ES",
        "name":"Example","geo_level":"city","geography_system":"OECD_FUA",
        "source_id":"OECD","source_geo_code":code,"parent_geo_id":"OECD_FUA:ES1F",
        "latitude":43.1,"longitude":-5.8,**kw}


def test_geography_bulk_write_rolls_back_if_later_row_invalid(isolated_db):
    first=geography("ES001C")
    invalid=geography("ES002C")
    invalid["source_geo_code"]=None
    with pytest.raises(Exception):
        analytics.upsert_geographies([first,invalid])
    con=duckdb.connect(str(isolated_db),read_only=True)
    try: assert con.execute("SELECT COUNT(*) FROM geography_registry WHERE geo_id = ?",[first["geo_id"]]).fetchone()[0]==0
    finally: con.close()


def test_geometry_bulk_write_rolls_back_if_later_row_invalid(isolated_db):
    rows=[]
    for code in ("ES001C","ES002C"):
        rows.append({"geo_id":"OECD_FUA:"+code,"country_iso3":"ESP","geography_system":"OECD_FUA",
          "geo_level":"city","source_geo_code":code,"geometry_geojson":'{"type":"Point","coordinates":[0,0]}',
          "source_id":"OECD","dataset_version":"test","retrieved_at":datetime.now(timezone.utc)})
    rows[1]["geometry_geojson"]=None
    with pytest.raises(Exception):
        analytics.upsert_geography_geometries(rows)
    con=duckdb.connect(str(isolated_db),read_only=True)
    try: assert con.execute("SELECT COUNT(*) FROM geography_geometries WHERE geo_id = ?",[rows[0]["geo_id"]]).fetchone()[0]==0
    finally: con.close()


def test_repeated_bootstrap_preserves_enriched_geography(isolated_db):
    code="ES001C"
    analytics.upsert_geographies([geography(code)])
    con=duckdb.connect(str(isolated_db))
    try:
        con.execute("""INSERT INTO subnational_observations
          (geography_system,geo_code,geo_name,geo_level,indicator_id,period,value,unit,source_id,dataset_id,retrieved_at)
          VALUES ('OECD_FUA',?,'Sample','city','urban_population',2025,100,'persons','OECD','test',?)""",
          [code,datetime.now(timezone.utc)])
    finally: con.close()
    analytics.initialize_analytics_schema()
    con=duckdb.connect(str(isolated_db),read_only=True)
    try:
        row=con.execute("SELECT parent_geo_id,latitude,longitude FROM geography_registry WHERE geo_id=?",
                        ["OECD_FUA:"+code]).fetchone()
        assert row==("OECD_FUA:ES1F",43.1,-5.8)
    finally: con.close()
