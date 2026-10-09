import duckdb

from app.core.config import settings
from app.services.geography_indicator_coverage import indicator_geography_coverage


def test_observed_geography_reach_uses_distinct_geographies_not_years(
    tmp_path, monkeypatch,
):
    db_path = tmp_path / "geography-coverage.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute("""
        CREATE TABLE geography_registry (
            geo_id VARCHAR, country_iso3 VARCHAR, geography_system VARCHAR,
            geo_level VARCHAR, source_geo_code VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE subnational_observations (
            geography_system VARCHAR, geo_code VARCHAR, geo_level VARCHAR,
            indicator_id VARCHAR, period INTEGER
        )
    """)
    con.executemany(
        "INSERT INTO geography_registry VALUES (?, ?, ?, ?, ?)",
        [
            ("one", "ESP", "OECD_TL", "tl2", "R1"),
            ("two", "ESP", "OECD_TL", "tl2", "R2"),
            ("three", "ESP", "OECD_TL", "tl2", "R3"),
            ("four", "PRT", "OECD_TL", "tl2", "R4"),
            ("other", "ESP", "NUTS_2024", "nuts2", "R1"),
        ],
    )
    con.executemany(
        "INSERT INTO subnational_observations VALUES (?, ?, ?, ?, ?)",
        [
            ("OECD_TL", "R1", "tl2", "regional_population", 2022),
            ("OECD_TL", "R1", "tl2", "regional_population", 2023),
            ("OECD_TL", "R2", "tl2", "regional_population", 2021),
            ("NUTS_2024", "R1", "nuts2", "regional_population", 2023),
            ("OECD_TL", "R4", "tl2", "regional_population", 2024),
        ],
    )
    con.close()
    monkeypatch.setattr(settings, "duckdb_path", db_path)
    response = indicator_geography_coverage(
        country_iso3="esp", geography_system="OECD_TL", geo_level="TL2"
    )
    assert response["indicator_count"] == 1
    row = response["items"][0]
    assert row["registered_geographies"] == 3
    assert row["covered_geographies"] == 2
    assert row["missing_geographies"] == 1
    assert row["coverage_ratio"] == 2 / 3
    assert row["oldest_latest_period"] == 2021
    assert row["newest_latest_period"] == 2023
    assert "coverage_band" not in row
    assert response["groups_without_observations"] == []


def test_registered_group_without_evidence_is_not_claimed_absent_by_indicator(
    tmp_path, monkeypatch,
):
    db_path = tmp_path / "empty-coverage.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute("""
        CREATE TABLE geography_registry (
            geo_id VARCHAR, country_iso3 VARCHAR, geography_system VARCHAR,
            geo_level VARCHAR, source_geo_code VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE subnational_observations (
            geography_system VARCHAR, geo_code VARCHAR, geo_level VARCHAR,
            indicator_id VARCHAR, period INTEGER
        )
    """)
    con.execute(
        "INSERT INTO geography_registry VALUES ('x', 'ESP', 'OECD_FUA', 'fua', 'FUA1')"
    )
    con.close()
    monkeypatch.setattr(settings, "duckdb_path", db_path)
    response = indicator_geography_coverage(country_iso3="ESP")
    assert response["items"] == []
    assert response["groups_without_observations"][0]["geo_level"] == "fua"
    assert response["groups_without_observations"][0]["registered_geographies"] == 1
