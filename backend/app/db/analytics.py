from datetime import datetime, timezone

import duckdb

from app.catalog import COUNTRIES, INDICATORS, SOURCES
from app.core.config import settings


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS countries (
    iso2 VARCHAR,
    iso3 VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    region VARCHAR,
    subregion VARCHAR,
    currency VARCHAR,
    eu_member BOOLEAN,
    eurozone_member BOOLEAN,
    oecd_member BOOLEAN
);

CREATE TABLE IF NOT EXISTS sources (
    source_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    organisation VARCHAR,
    base_url VARCHAR,
    priority INTEGER
);

CREATE TABLE IF NOT EXISTS indicators (
    indicator_id VARCHAR PRIMARY KEY,
    source_indicator VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    dimension VARCHAR NOT NULL,
    unit VARCHAR,
    higher_is_better BOOLEAN
);

CREATE TABLE IF NOT EXISTS observations (
    country_iso3 VARCHAR NOT NULL,
    indicator_id VARCHAR NOT NULL,
    period INTEGER NOT NULL,
    value DOUBLE NOT NULL,
    unit VARCHAR,
    source_id VARCHAR NOT NULL,
    dataset_id VARCHAR,
    observation_type VARCHAR NOT NULL,
    retrieved_at TIMESTAMP NOT NULL,
    source_updated_at VARCHAR,
    source_observation_status VARCHAR,
    source_decimal INTEGER,
    PRIMARY KEY (country_iso3, indicator_id, period, source_id)
);
"""


def initialize_analytics_schema() -> None:
    con = duckdb.connect(str(settings.duckdb_path))
    try:
        con.execute(SCHEMA_SQL)

        for country in COUNTRIES:
            con.execute(
                """
                INSERT OR REPLACE INTO countries
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    country["iso2"],
                    country["iso3"],
                    country["name"],
                    country["region"],
                    country["subregion"],
                    country["currency"],
                    country["eu_member"],
                    country["eurozone_member"],
                    country["oecd_member"],
                ],
            )

        for source in SOURCES:
            con.execute(
                "INSERT OR REPLACE INTO sources VALUES (?, ?, ?, ?, ?)",
                [
                    source["source_id"],
                    source["name"],
                    source["organisation"],
                    source["base_url"],
                    source["priority"],
                ],
            )

        for indicator in INDICATORS:
            con.execute(
                "INSERT OR REPLACE INTO indicators VALUES (?, ?, ?, ?, ?, ?)",
                [
                    indicator["indicator_id"],
                    indicator["source_indicator"],
                    indicator["name"],
                    indicator["dimension"],
                    indicator["unit"],
                    indicator["higher_is_better"],
                ],
            )
    finally:
        con.close()


def upsert_observations(rows: list[dict]) -> int:
    if not rows:
        return 0

    con = duckdb.connect(str(settings.duckdb_path))
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO observations
            (
                country_iso3, indicator_id, period, value, unit,
                source_id, dataset_id, observation_type, retrieved_at,
                source_updated_at, source_observation_status, source_decimal
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                [
                    row["country_iso3"],
                    row["indicator_id"],
                    row["period"],
                    row["value"],
                    row["unit"],
                    row["source_id"],
                    row["dataset_id"],
                    row["observation_type"],
                    row["retrieved_at"],
                    row.get("source_updated_at"),
                    row.get("source_observation_status"),
                    row.get("source_decimal"),
                ]
                for row in rows
            ],
        )
        return len(rows)
    finally:
        con.close()


def latest_observations(country_iso3: str) -> list[dict]:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            WITH ranked AS (
                SELECT
                    o.country_iso3,
                    o.indicator_id,
                    i.name,
                    i.dimension,
                    o.period,
                    o.value,
                    o.unit,
                    o.source_id,
                    o.retrieved_at,
                    o.source_updated_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY o.indicator_id
                        ORDER BY o.period DESC
                    ) AS rn
                FROM observations o
                JOIN indicators i USING (indicator_id)
                WHERE o.country_iso3 = ?
            )
            SELECT
                country_iso3, indicator_id, name, dimension, period,
                value, unit, source_id, retrieved_at, source_updated_at
            FROM ranked
            WHERE rn = 1
            ORDER BY dimension, indicator_id
            """,
            [country_iso3.upper()],
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()


def country_registry() -> list[dict]:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            SELECT iso2, iso3, name, region, subregion, currency,
                   eu_member, eurozone_member, oecd_member
            FROM countries
            ORDER BY name
            """
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()


def indicator_registry() -> list[dict]:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            SELECT indicator_id, source_indicator, name, dimension, unit, higher_is_better
            FROM indicators
            ORDER BY dimension, indicator_id
            """
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()


def indicator_series(country_iso3: str, indicator_id: str) -> list[dict]:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            SELECT period, value, unit, source_id, retrieved_at, source_updated_at
            FROM observations
            WHERE country_iso3 = ? AND indicator_id = ?
            ORDER BY period
            """,
            [country_iso3.upper(), indicator_id],
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()
