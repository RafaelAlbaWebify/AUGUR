from datetime import datetime, timezone
from types import SimpleNamespace

import duckdb

from app.db import analytics as module


def test_subnational_status_counts_nuts2_nuts3_and_city_case_insensitively(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "subnational.duckdb"
    con = duckdb.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE subnational_observations (
                geography_system TEXT,
                geo_code TEXT,
                geo_level TEXT,
                indicator_id TEXT,
                retrieved_at TIMESTAMP
            )
            """
        )
        now = datetime.now(timezone.utc)
        con.executemany(
            """
            INSERT INTO subnational_observations
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("NUTS_2024", "ES12", "NUTS2", "regional_employment_rate", now),
                ("NUTS_2024", "PT11", "nuts2", "regional_unemployment_rate", now),
                ("NUTS_2024", "ES120", "NUTS3", "regional_robbery_rate", now),
                ("NUTS_2024", "IE061", "nuts3", "regional_intentional_homicide_rate", now),
                ("URBAN_AUDIT_2024", "ES013C", "city", "city_population", now),
                ("URBAN_AUDIT_2024", "PT001C", "CITY", "city_population", now),
            ],
        )
    finally:
        con.close()

    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(duckdb_path=path),
    )

    overall = module.subnational_storage_status()
    by_level = module.subnational_evidence_by_level_status()

    assert overall == {
        "observation_count": 6,
        "geography_count": 6,
        "nuts2_count": 2,
        "nuts3_count": 2,
        "city_count": 2,
    }
    assert by_level["NUTS2"]["geography_count"] == 2
    assert by_level["NUTS3"]["geography_count"] == 2
    assert by_level["CITY"]["geography_count"] == 2
    assert by_level["NUTS3"]["indicator_ids"] == [
        "regional_intentional_homicide_rate",
        "regional_robbery_rate",
    ]


def test_subnational_indicator_series_returns_recent_points_in_time_order(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "regional-history.duckdb"
    con = duckdb.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE subnational_observations (
                geography_system TEXT,
                geo_code TEXT,
                geo_name TEXT,
                geo_level TEXT,
                indicator_id TEXT,
                period INTEGER,
                value DOUBLE,
                unit TEXT,
                source_id TEXT,
                dataset_id TEXT,
                retrieved_at TIMESTAMP,
                source_updated_at TEXT
            )
            """
        )
        now = datetime.now(timezone.utc)
        rows = [
            ("NUTS_2024", "ES12", "Asturias", "NUTS2", "regional_employment_rate", year, value, "percent", "EUROSTAT", "lfst_r_lfe2emprt", now, None)
            for year, value in [
                (2019, 64.0),
                (2020, 63.0),
                (2021, 65.0),
                (2022, 67.0),
                (2023, 69.0),
                (2024, 70.5),
                (2025, 72.0),
            ]
        ]
        con.executemany(
            "INSERT INTO subnational_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
    finally:
        con.close()

    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(duckdb_path=path),
    )

    series = module.subnational_indicator_series("ES12", max_points=4)

    assert [row["period"] for row in series] == [2022, 2023, 2024, 2025]
    assert [row["value"] for row in series] == [67.0, 69.0, 70.5, 72.0]


def test_geography_registry_reports_provider_neutral_coverage(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "geography-coverage.duckdb"
    con = duckdb.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE geography_registry (
                geo_id VARCHAR PRIMARY KEY,
                country_iso3 VARCHAR,
                country_iso2 VARCHAR,
                name VARCHAR,
                geo_level VARCHAR,
                geography_system VARCHAR,
                source_id VARCHAR,
                source_geo_code VARCHAR,
                parent_geo_id VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE
            )
            """
        )
        con.execute(
            """
            CREATE TABLE subnational_observations (
                geography_system VARCHAR,
                geo_code VARCHAR,
                indicator_id VARCHAR,
                dataset_id VARCHAR,
                period INTEGER
            )
            """
        )
        con.executemany(
            "INSERT INTO geography_registry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("ES12", "ESP", "ES", "Asturias", "nuts2", "NUTS_2024", "EUROSTAT", "ES12", None, None, None),
                ("ES013C", "ESP", "ES", "Oviedo", "city", "URBAN_AUDIT_2024", "EUROSTAT", "ES013C", None, None, None),
                ("US-CA", "USA", "US", "California", "admin1", "ISO_3166_2", "TEST", "US-CA", None, None, None),
            ],
        )
        con.executemany(
            "INSERT INTO subnational_observations VALUES (?, ?, ?, ?, ?)",
            [
                ("NUTS_2024", "ES12", "regional_population", "demo_r_d2jan", 2024),
                ("URBAN_AUDIT_2024", "ES013C", "city_population", "urb_cpop1", 2024),
                ("ISO_3166_2", "US-CA", "regional_population", "TEST_REGIONAL", 2024),
            ],
        )
    finally:
        con.close()

    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(duckdb_path=path),
    )

    result = module.geography_coverage_status()

    assert result["countries_with_subnational_evidence"] == 2
    assert result["geography_count"] == 3
    assert result["systems"] == ["ISO_3166_2", "NUTS_2024", "URBAN_AUDIT_2024"]
    assert {"nuts2", "city", "admin1"} == set(result["levels"])


def test_geographies_for_country_returns_only_analyzable_rows(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "country-geographies.duckdb"
    con = duckdb.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE geography_registry (
                geo_id VARCHAR PRIMARY KEY,
                country_iso3 VARCHAR,
                country_iso2 VARCHAR,
                name VARCHAR,
                geo_level VARCHAR,
                geography_system VARCHAR,
                source_id VARCHAR,
                source_geo_code VARCHAR,
                parent_geo_id VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE
            )
            """
        )
        con.execute(
            """
            CREATE TABLE subnational_observations (
                geography_system VARCHAR,
                geo_code VARCHAR,
                indicator_id VARCHAR,
                period INTEGER
            )
            """
        )
        con.executemany(
            "INSERT INTO geography_registry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("OECD_TL_2024:AU1", "AUS", "AU", "New South Wales", "tl2", "OECD_TL_2024", "OECD", "AU1", None, None, None),
                ("OECD_TL_2024:AU2", "AUS", "AU", "Victoria", "tl2", "OECD_TL_2024", "OECD", "AU2", None, None, None),
                ("OECD_TL_2024:AU3", "AUS", "AU", "Queensland", "tl2", "OECD_TL_2024", "OECD", "AU3", None, None, None),
                ("NUTS_2024:ES12", "ESP", "ES", "Asturias", "nuts2", "NUTS_2024", "EUROSTAT", "ES12", None, None, None),
            ],
        )
        con.executemany(
            "INSERT INTO subnational_observations VALUES (?, ?, ?, ?)",
            [
                ("OECD_TL_2024", "AU1", "regional_population_density", 2024),
                ("OECD_TL_2024", "AU2", "regional_population_density", 2024),
                ("NUTS_2024", "ES12", "regional_population_density", 2024),
            ],
        )
    finally:
        con.close()

    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(duckdb_path=path),
    )

    rows = module.geographies_for_country("AUS")

    assert [row["source_geo_code"] for row in rows] == ["AU1", "AU2"]
    assert [row["name"] for row in rows] == ["New South Wales", "Victoria"]
    assert all(row["geography_system"] == "OECD_TL_2024" for row in rows)
    assert all(row["geo_level"] == "tl2" for row in rows)
    assert all(row["indicator_count"] == 1 for row in rows)
    assert all(row["latest_period"] == 2024 for row in rows)



def test_same_source_code_isolated_by_geography_system(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "system-isolation.duckdb"
    con = duckdb.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE subnational_observations (
                geography_system VARCHAR,
                geo_code VARCHAR,
                geo_name VARCHAR,
                geo_level VARCHAR,
                indicator_id VARCHAR,
                period INTEGER,
                value DOUBLE,
                unit VARCHAR,
                source_id VARCHAR,
                dataset_id VARCHAR,
                retrieved_at TIMESTAMP,
                source_updated_at VARCHAR
            )
            """
        )
        now = datetime.now(timezone.utc)
        con.executemany(
            "INSERT INTO subnational_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    "OECD_TL_2024",
                    "X1",
                    "OECD Example",
                    "tl2",
                    "regional_population_density",
                    2024,
                    10.0,
                    "people_per_km2",
                    "OECD",
                    "oecd-density",
                    now,
                    None,
                ),
                (
                    "ISO_3166_2",
                    "X1",
                    "Admin Example",
                    "admin1",
                    "regional_population_density",
                    2024,
                    20.0,
                    "people_per_km2",
                    "TEST",
                    "admin-density",
                    now,
                    None,
                ),
            ],
        )
    finally:
        con.close()

    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(duckdb_path=path),
    )

    oecd = module.latest_subnational_observations(
        "X1",
        geography_system="OECD_TL_2024",
    )
    admin = module.latest_subnational_observations(
        "X1",
        geography_system="ISO_3166_2",
    )

    assert len(oecd) == 1
    assert len(admin) == 1
    assert oecd[0]["value"] == 10.0
    assert admin[0]["value"] == 20.0
    assert oecd[0]["geography_system"] == "OECD_TL_2024"
    assert admin[0]["geography_system"] == "ISO_3166_2"


def test_geography_geometry_storage_round_trip(monkeypatch, tmp_path):
    path = tmp_path / "geography-geometry.duckdb"
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(duckdb_path=path),
    )
    module.initialize_analytics_schema()

    stored = module.upsert_geography_geometries([
        {
            "geo_id": "OECD_FUA:AUS01F",
            "country_iso3": "AUS",
            "geography_system": "OECD_FUA",
            "geo_level": "fua",
            "source_geo_code": "AUS01F",
            "geometry_geojson": (
                '{"type":"Polygon","coordinates":'
                '[[[151.0,-34.0],[151.5,-34.0],'
                '[151.5,-33.5],[151.0,-34.0]]]}'
            ),
            "bbox_min_lon": 151.0,
            "bbox_min_lat": -34.0,
            "bbox_max_lon": 151.5,
            "bbox_max_lat": -33.5,
            "source_id": "OECD",
            "dataset_version": "official-boundaries",
        }
    ])

    assert stored == 1

    rows = module.geography_geometries_for_country(
        "AUS",
        geography_system="OECD_FUA",
    )
    assert len(rows) == 1
    assert rows[0]["geo_id"] == "OECD_FUA:AUS01F"
    assert rows[0]["source_geo_code"] == "AUS01F"
    assert rows[0]["geo_level"] == "fua"

    coverage = module.geography_geometry_coverage_status()
    assert coverage["geometry_count"] == 1
    assert coverage["countries_with_geometry"] == 1
    assert coverage["systems"] == ["OECD_FUA"]


def test_stale_geography_countries_respects_freshness_window(
    monkeypatch,
    tmp_path,
):
    from datetime import timedelta

    path = tmp_path / "geography-freshness.duckdb"
    con = duckdb.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE geography_registry (
                geo_id VARCHAR PRIMARY KEY,
                country_iso3 VARCHAR,
                country_iso2 VARCHAR,
                name VARCHAR,
                geo_level VARCHAR,
                geography_system VARCHAR,
                source_id VARCHAR,
                source_geo_code VARCHAR,
                parent_geo_id VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE
            )
            """
        )
        con.execute(
            """
            CREATE TABLE subnational_observations (
                geography_system VARCHAR,
                geo_code VARCHAR,
                indicator_id VARCHAR,
                retrieved_at TIMESTAMP
            )
            """
        )
        now = datetime.now(timezone.utc)
        con.executemany(
            "INSERT INTO geography_registry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("OECD_TL_2024:AU1", "AUS", "AU", "New South Wales", "tl2", "OECD_TL_2024", "OECD", "AU1", None, None, None),
                ("OECD_TL_2024:CA1", "CAN", "CA", "Ontario", "tl2", "OECD_TL_2024", "OECD", "CA1", None, None, None),
                ("OECD_TL_2024:JP1", "JPN", "JP", "Japan region", "tl2", "OECD_TL_2024", "OECD", "JP1", None, None, None),
            ],
        )
        con.executemany(
            "INSERT INTO subnational_observations VALUES (?, ?, ?, ?)",
            [
                ("OECD_TL_2024", "AU1", "regional_population", now),
                ("OECD_TL_2024", "CA1", "regional_population", now - timedelta(hours=30)),
            ],
        )
    finally:
        con.close()

    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(duckdb_path=path),
    )

    stale = module.stale_geography_countries(
        "OECD_TL_2024",
        {"AUS", "CAN", "JPN"},
        [],
        max_age_hours=24,
    )

    assert stale == {"CAN", "JPN"}


def test_stale_geography_countries_can_require_specific_indicators(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "geography-required-indicators.duckdb"
    con = duckdb.connect(str(path))
    try:
        con.execute(
            """
            CREATE TABLE geography_registry (
                geo_id VARCHAR PRIMARY KEY,
                country_iso3 VARCHAR,
                country_iso2 VARCHAR,
                name VARCHAR,
                geo_level VARCHAR,
                geography_system VARCHAR,
                source_id VARCHAR,
                source_geo_code VARCHAR,
                parent_geo_id VARCHAR,
                latitude DOUBLE,
                longitude DOUBLE
            )
            """
        )
        con.execute(
            """
            CREATE TABLE subnational_observations (
                geography_system VARCHAR,
                geo_code VARCHAR,
                indicator_id VARCHAR,
                retrieved_at TIMESTAMP
            )
            """
        )
        now = datetime.now(timezone.utc)
        con.execute(
            "INSERT INTO geography_registry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ["OECD_FUA:AUS01F", "AUS", "AU", "Sydney FUA", "fua", "OECD_FUA", "OECD", "AUS01F", None, None, None],
        )
        con.execute(
            "INSERT INTO subnational_observations VALUES (?, ?, ?, ?)",
            ["OECD_FUA", "AUS01F", "urban_population", now],
        )
    finally:
        con.close()

    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(duckdb_path=path),
    )

    stale = module.stale_geography_countries(
        "OECD_FUA",
        {"AUS"},
        {"urban_population", "urban_population_density"},
        max_age_hours=24,
    )

    assert stale == {"AUS"}
