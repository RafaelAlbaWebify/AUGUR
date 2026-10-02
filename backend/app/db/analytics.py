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
    interpretation_policy VARCHAR,
    target_min DOUBLE,
    target_max DOUBLE
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

CREATE TABLE IF NOT EXISTS labour_earnings (
    country_iso3 VARCHAR NOT NULL,
    period INTEGER NOT NULL,
    isco08 VARCHAR NOT NULL,
    value DOUBLE NOT NULL,
    unit VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    dataset_id VARCHAR NOT NULL,
    retrieved_at TIMESTAMP NOT NULL,
    source_updated_at VARCHAR,
    PRIMARY KEY (country_iso3, period, isco08, source_id)
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

        existing_columns = {
            row[1]
            for row in con.execute("PRAGMA table_info('indicators')").fetchall()
        }

        if "interpretation_policy" not in existing_columns:
            con.execute("ALTER TABLE indicators ADD COLUMN interpretation_policy VARCHAR")
        if "target_min" not in existing_columns:
            con.execute("ALTER TABLE indicators ADD COLUMN target_min DOUBLE")
        if "target_max" not in existing_columns:
            con.execute("ALTER TABLE indicators ADD COLUMN target_max DOUBLE")

        for indicator in INDICATORS:
            con.execute(
                """
                INSERT OR REPLACE INTO indicators
                (
                    indicator_id, source_indicator, name, dimension, unit,
                    interpretation_policy, target_min, target_max
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    indicator["indicator_id"],
                    indicator["source_indicator"],
                    indicator["name"],
                    indicator["dimension"],
                    indicator["unit"],
                    indicator["interpretation_policy"],
                    indicator["target_min"],
                    indicator["target_max"],
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



def upsert_labour_earnings(rows: list[dict]) -> int:
    if not rows:
        return 0

    con = duckdb.connect(str(settings.duckdb_path))
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO labour_earnings
            (
                country_iso3, period, isco08, value, unit,
                source_id, dataset_id, retrieved_at, source_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                [
                    row["country_iso3"],
                    row["period"],
                    row["isco08"],
                    row["value"],
                    row["unit"],
                    row["source_id"],
                    row["dataset_id"],
                    row["retrieved_at"],
                    row.get("source_updated_at"),
                ]
                for row in rows
            ],
        )
        return len(rows)
    finally:
        con.close()


def latest_labour_earnings(
    country_iso3: str,
    isco08: str | None = None,
) -> list[dict]:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        params: list[str] = [country_iso3.upper()]
        isco_filter = ""
        if isco08:
            isco_filter = "AND isco08 = ?"
            params.append(isco08.upper())

        result = con.execute(
            f"""
            WITH ranked AS (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY isco08
                        ORDER BY period DESC, source_id ASC
                    ) AS rn
                FROM labour_earnings
                WHERE country_iso3 = ?
                {isco_filter}
            )
            SELECT
                country_iso3, period, isco08, value, unit,
                source_id, dataset_id, retrieved_at, source_updated_at
            FROM ranked
            WHERE rn = 1
            ORDER BY isco08
            """,
            params,
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
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
                        ORDER BY o.period DESC, s.priority ASC, o.source_id ASC
                    ) AS rn
                FROM observations o
                JOIN indicators i USING (indicator_id)
                JOIN sources s USING (source_id)
                WHERE o.country_iso3 = ?
                  AND o.observation_type = 'observed'
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
            SELECT indicator_id, source_indicator, name, dimension, unit,
                   interpretation_policy, target_min, target_max
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
            WITH ranked AS (
                SELECT
                    o.period,
                    o.value,
                    o.unit,
                    o.source_id,
                    o.retrieved_at,
                    o.source_updated_at,
                    s.priority,
                    ROW_NUMBER() OVER (
                        PARTITION BY o.period
                        ORDER BY s.priority ASC, o.source_id ASC
                    ) AS rn
                FROM observations o
                JOIN sources s USING (source_id)
                WHERE o.country_iso3 = ?
                  AND o.indicator_id = ?
                  AND o.observation_type = 'observed'
            )
            SELECT period, value, unit, source_id, retrieved_at, source_updated_at
            FROM ranked
            WHERE rn = 1
            ORDER BY period
            """,
            [country_iso3.upper(), indicator_id],
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()


def indicator_source_comparison(country_iso3: str) -> list[dict]:
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
                    s.name AS source_name,
                    s.priority AS source_priority,
                    o.dataset_id,
                    o.retrieved_at,
                    o.source_updated_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY o.indicator_id, o.source_id
                        ORDER BY o.period DESC
                    ) AS rn
                FROM observations o
                JOIN indicators i USING (indicator_id)
                JOIN sources s USING (source_id)
                WHERE o.country_iso3 = ?
                  AND o.observation_type = 'observed'
            )
            SELECT
                country_iso3, indicator_id, name, dimension,
                period, value, unit, source_id, source_name,
                source_priority, dataset_id, retrieved_at, source_updated_at
            FROM ranked
            WHERE rn = 1
            ORDER BY indicator_id, source_priority, source_id
            """,
            [country_iso3.upper()],
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()


def source_quality_summary(country_iso3: str) -> list[dict]:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            WITH observed AS (
                SELECT
                    o.country_iso3,
                    o.indicator_id,
                    i.name,
                    i.dimension,
                    o.period,
                    o.value,
                    o.unit,
                    o.source_id,
                    s.name AS source_name,
                    s.priority AS source_priority
                FROM observations o
                JOIN indicators i USING (indicator_id)
                JOIN sources s USING (source_id)
                WHERE o.country_iso3 = ?
                  AND o.observation_type = 'observed'
            ),
            latest_by_source AS (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY indicator_id, source_id
                        ORDER BY period DESC
                    ) AS rn
                FROM observed
            ),
            latest AS (
                SELECT *
                FROM latest_by_source
                WHERE rn = 1
            ),
            latest_summary AS (
                SELECT
                    indicator_id,
                    MIN(name) AS name,
                    MIN(dimension) AS dimension,
                    MIN(unit) AS unit,
                    COUNT(*) AS source_count,
                    MIN_BY(source_id, source_priority) AS preferred_source_id,
                    MIN_BY(source_name, source_priority) AS preferred_source_name,
                    MIN_BY(period, source_priority) AS preferred_period,
                    MIN_BY(value, source_priority) AS preferred_value,
                    MAX(period) AS freshest_period,
                    MAX(period) - MIN(period) AS period_spread
                FROM latest
                GROUP BY indicator_id
            ),
            common_periods AS (
                SELECT
                    indicator_id,
                    period,
                    COUNT(DISTINCT source_id) AS common_source_count
                FROM observed
                GROUP BY indicator_id, period
                HAVING COUNT(DISTINCT source_id) >= 2
            ),
            latest_common_period AS (
                SELECT
                    indicator_id,
                    MAX(period) AS common_period
                FROM common_periods
                GROUP BY indicator_id
            ),
            common_values AS (
                SELECT
                    o.indicator_id,
                    o.period AS common_period,
                    COUNT(DISTINCT o.source_id) AS common_period_source_count,
                    MIN(o.value) AS min_value,
                    MAX(o.value) AS max_value,
                    MIN_BY(o.value, o.source_priority) AS preferred_common_value
                FROM observed o
                JOIN latest_common_period cp
                  ON cp.indicator_id = o.indicator_id
                 AND cp.common_period = o.period
                GROUP BY o.indicator_id, o.period
            )
            SELECT
                ls.indicator_id,
                ls.name,
                ls.dimension,
                ls.unit,
                ls.source_count,
                ls.preferred_source_id,
                ls.preferred_source_name,
                ls.preferred_period,
                ls.preferred_value,
                ls.freshest_period,
                ls.period_spread,
                cv.common_period,
                cv.common_period_source_count,
                CASE
                    WHEN cv.common_period_source_count < 2 THEN NULL
                    WHEN cv.preferred_common_value = 0 THEN NULL
                    ELSE (
                        (cv.max_value - cv.min_value)
                        / ABS(cv.preferred_common_value)
                    ) * 100
                END AS disagreement_pct
            FROM latest_summary ls
            LEFT JOIN common_values cv USING (indicator_id)
            ORDER BY ls.indicator_id
            """,
            [country_iso3.upper()],
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()


def official_forecasts(country_iso3: str) -> list[dict]:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            SELECT
                o.country_iso3,
                o.indicator_id,
                i.name,
                i.dimension,
                o.period,
                o.value,
                o.unit,
                o.source_id,
                s.name AS source_name,
                o.dataset_id,
                o.source_updated_at
            FROM observations o
            JOIN indicators i USING (indicator_id)
            JOIN sources s USING (source_id)
            WHERE o.country_iso3 = ?
              AND o.observation_type = 'official_forecast'
            ORDER BY o.indicator_id, o.period
            """,
            [country_iso3.upper()],
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()


def future_trajectory(country_iso3: str, horizons: list[int]) -> list[dict]:
    if not horizons:
        return []

    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        placeholders = ",".join(["?"] * len(horizons))
        result = con.execute(
            f"""
            SELECT
                o.country_iso3,
                o.indicator_id,
                i.name,
                i.dimension,
                o.period,
                o.value,
                o.unit,
                o.source_id,
                s.name AS source_name,
                o.dataset_id,
                o.observation_type,
                o.source_updated_at
            FROM observations o
            JOIN indicators i USING (indicator_id)
            JOIN sources s USING (source_id)
            WHERE o.country_iso3 = ?
              AND o.observation_type = 'official_forecast'
              AND o.period IN ({placeholders})
            ORDER BY o.period, i.dimension, o.indicator_id, s.priority, o.source_id
            """,
            [country_iso3.upper(), *horizons],
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()
