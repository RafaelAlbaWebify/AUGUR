"""GR-2 tests: no implicit vintage certification, deterministic page, read-only."""
import duckdb
import json
import pytest
from app.services.regional_rankings import regional_rankings


def make_db(path):
    con = duckdb.connect(str(path))
    con.execute("""CREATE TABLE geography_registry (
        geo_id VARCHAR, country_iso3 VARCHAR, name VARCHAR,
        geography_system VARCHAR, source_geo_code VARCHAR, geo_level VARCHAR
    )""")
    con.execute("""CREATE TABLE subnational_observations (
        geography_system VARCHAR, geo_code VARCHAR, geo_level VARCHAR,
        indicator_id VARCHAR, period INTEGER, unit VARCHAR,
        source_id VARCHAR, dataset_id VARCHAR, value DOUBLE,
        response_dimensions_json VARCHAR, source_observation_status VARCHAR
    )""")
    for geo_id, country, geo_code, val in (
        ("ES11", "ESP", "ES11", 7.1),
        ("PT11", "PRT", "PT11", 4.0),
        ("IE04", "IRL", "IE04", 4.0),
    ):
        con.execute("INSERT INTO geography_registry VALUES (?, ?, ?, 'NUTS_2024', ?, 'nuts2')",
                    [geo_id, country, geo_id, geo_code])
        con.execute("""INSERT INTO subnational_observations VALUES
            ('NUTS_2024', ?, 'nuts2', 'regional_unemployment_rate',
             2025, 'percent', 'EUROSTAT', 'lfst_r_lfu3rt', ?, ?, NULL)""",
                    [geo_code, val, json.dumps({"geo": geo_code, "time": "2025",
                        "freq": "A", "age": "Y20-64", "sex": "T", "unit": "PC"})])
    con.close()


def test_public_safe_default_rejects_unverified_vintages(tmp_path):
    db = tmp_path / "audit.duckdb"
    make_db(db)
    before = db.stat().st_size
    result = regional_rankings("regional_unemployment_rate", db_path=db)
    assert result["status"] == "blocked_unverified_evidence"
    assert result["observed_rows"] == 3
    assert result["eligible_total"] == 0
    assert result["excluded_reasons"] == {"unverified_boundary_vintage": 3}
    assert result["items"] == []
    assert db.stat().st_size == before


def test_verified_fixture_order_and_global_pagination(tmp_path):
    db = tmp_path / "audit.duckdb"
    make_db(db)
    result = regional_rankings(
        "regional_unemployment_rate", db_path=db,
        verified_geo_ids=frozenset({"ES11", "PT11", "IE04"}),
        limit=1, offset=1,
    )
    assert result["status"] == "ready"
    assert result["eligible_total"] == 3
    assert result["items"][0]["geo_id"] == "PT11"
    assert result["items"][0]["rank"] == 2
    assert result["has_more"]


def test_rejects_unregistered_metric_and_bad_page(tmp_path):
    with pytest.raises(ValueError):
        regional_rankings("not_a_metric", db_path=tmp_path / "none.duckdb")
    with pytest.raises(ValueError):
        regional_rankings("regional_unemployment_rate", limit=0, db_path=tmp_path / "none.duckdb")


def test_missing_response_dimensions_block_certified_rows(tmp_path):
    db = tmp_path / "audit.duckdb"
    make_db(db)
    con = duckdb.connect(str(db))
    con.execute("UPDATE subnational_observations SET response_dimensions_json=NULL")
    con.close()
    result = regional_rankings("regional_unemployment_rate", db_path=db,
                               verified_geo_ids=frozenset({"ES11", "PT11", "IE04"}))
    assert result["eligible_total"] == 0
    assert result["provider_metadata_issues"] == {"missing_response_dimensions": 3}
