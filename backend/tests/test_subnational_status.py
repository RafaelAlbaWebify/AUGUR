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
            VALUES (?, ?, ?, ?)
            """,
            [
                ("ES12", "NUTS2", "regional_employment_rate", now),
                ("PT11", "nuts2", "regional_unemployment_rate", now),
                ("ES120", "NUTS3", "regional_robbery_rate", now),
                ("IE061", "nuts3", "regional_intentional_homicide_rate", now),
                ("ES013C", "city", "city_population", now),
                ("PT001C", "CITY", "city_population", now),
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
                geo_code TEXT,
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
            ("ES12", "NUTS2", "regional_employment_rate", year, value, "percent", "EUROSTAT", "lfst_r_lfe2emprt", now, None)
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
            "INSERT INTO subnational_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                geo_code VARCHAR,
                indicator_id VARCHAR
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
            "INSERT INTO subnational_observations VALUES (?, ?)",
            [
                ("ES12", "regional_population"),
                ("ES013C", "city_population"),
                ("US-CA", "regional_population"),
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
