from pathlib import Path

import duckdb
import pytest

from scripts.audit_legacy_nuts_vintage import classify_claims, load_local_claims
from scripts.reconcile_legacy_nuts_vintage import preflight, reconcile_copy


OFFICIAL = {"nuts2": {"IE04", "PT19"}, "nuts3": {"IE041"}}


def fixture_database(path: Path, with_collision=False):
    con = duckdb.connect(str(path))
    con.execute("""
        CREATE TABLE subnational_observations (
            geography_system VARCHAR NOT NULL, geo_code VARCHAR NOT NULL,
            geo_name VARCHAR, geo_level VARCHAR NOT NULL,
            indicator_id VARCHAR NOT NULL, period INTEGER NOT NULL,
            value DOUBLE NOT NULL, unit VARCHAR,
            source_id VARCHAR NOT NULL, dataset_id VARCHAR NOT NULL,
            retrieved_at TIMESTAMP NOT NULL, source_updated_at VARCHAR,
            PRIMARY KEY(geography_system, geo_code, indicator_id, period, source_id)
        )
    """)
    con.execute("""
        CREATE TABLE geography_registry (
            geo_id VARCHAR PRIMARY KEY, country_iso3 VARCHAR, country_iso2 VARCHAR,
            name VARCHAR, geo_level VARCHAR NOT NULL, geography_system VARCHAR NOT NULL,
            source_id VARCHAR, source_geo_code VARCHAR NOT NULL,
            parent_geo_id VARCHAR, latitude DOUBLE, longitude DOUBLE
        )
    """)
    for code, system in [("IE01", "NUTS_2024"), ("IE04", "NUTS_2024")]:
        con.execute("""
            INSERT INTO subnational_observations
            (geography_system, geo_code, geo_level, indicator_id, period, value,
             source_id, dataset_id, retrieved_at)
            VALUES (?, ?, 'nuts2', 'employment', 2000, 52, 'EUROSTAT',
                    'lfst_r_lfe2emprt', CURRENT_TIMESTAMP)
        """, [system, code])
        con.execute("""
            INSERT INTO geography_registry
            (geo_id, country_iso2, geo_level, geography_system, source_id, source_geo_code)
            VALUES (?, 'IE', 'nuts2', ?, 'EUROSTAT', ?)
        """, [f"{system}:{code}", system, code])
    if with_collision:
        con.execute("""
            INSERT INTO subnational_observations
            (geography_system, geo_code, geo_level, indicator_id, period, value,
             source_id, dataset_id, retrieved_at)
            VALUES ('NUTS_UNSPECIFIED', 'IE01', 'nuts2', 'employment',
                    2000, 52, 'EUROSTAT', 'lfst_r_lfe2emprt', CURRENT_TIMESTAMP)
        """)
    con.close()


def snapshot(path):
    obs, registry = load_local_claims(path)
    return classify_claims(OFFICIAL, obs, registry)


def test_reconcile_copy_preserves_source_and_current_codes(tmp_path):
    source = tmp_path / "source.duckdb"
    output = tmp_path / "reconciled.duckdb"
    fixture_database(source)
    report = snapshot(source)
    plan = preflight(source, report, OFFICIAL)
    assert plan == {"observation_rows": 1, "registry_rows": 1, "codes": ["IE01"]}
    result = reconcile_copy(source, output, plan)
    assert result["observation_rows_relabelled"] == 1
    assert result["total_observations_preserved"] == 2
    assert len(snapshot(source)["definite_observation_mislabels"]) == 1
    assert not snapshot(output)["definite_observation_mislabels"]
    con = duckdb.connect(str(output), read_only=True)
    try:
        assert con.execute("""
            SELECT geography_system FROM subnational_observations
            WHERE geo_code = 'IE01'
        """).fetchone()[0] == "NUTS_UNSPECIFIED"
        assert con.execute("""
            SELECT geography_system FROM subnational_observations
            WHERE geo_code = 'IE04'
        """).fetchone()[0] == "NUTS_2024"
        assert con.execute("SELECT COUNT(*) FROM geography_registry").fetchone()[0] == 1
    finally:
        con.close()


def test_stale_report_fails_closed(tmp_path):
    source = tmp_path / "source.duckdb"
    fixture_database(source)
    report = snapshot(source)
    report["definite_observation_mislabels"][0]["observation_count"] = 999
    with pytest.raises(ValueError, match="no longer matches"):
        preflight(source, report, OFFICIAL)


def test_primary_key_collision_fails_closed(tmp_path):
    source = tmp_path / "source.duckdb"
    fixture_database(source, with_collision=True)
    with pytest.raises(ValueError, match="collision"):
        preflight(source, snapshot(source), OFFICIAL)


def test_output_is_never_overwritten(tmp_path):
    source = tmp_path / "source.duckdb"
    output = tmp_path / "existing.duckdb"
    fixture_database(source)
    output.write_text("do not overwrite")
    with pytest.raises(FileExistsError):
        reconcile_copy(source, output, preflight(source, snapshot(source), OFFICIAL))
    assert output.read_text() == "do not overwrite"
