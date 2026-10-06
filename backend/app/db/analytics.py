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

CREATE TABLE IF NOT EXISTS labour_net_earnings_reference (
    country_iso3 VARCHAR NOT NULL,
    period INTEGER NOT NULL,
    earnings_case VARCHAR NOT NULL,
    annual_net_eur DOUBLE NOT NULL,
    source_id VARCHAR NOT NULL,
    dataset_id VARCHAR NOT NULL,
    retrieved_at TIMESTAMP NOT NULL,
    source_updated_at VARCHAR,
    PRIMARY KEY (country_iso3, period, earnings_case, source_id)
);

CREATE TABLE IF NOT EXISTS labour_job_vacancy_rates (
    country_iso3 VARCHAR NOT NULL,
    period VARCHAR NOT NULL,
    isco08 VARCHAR NOT NULL,
    vacancy_rate_pct DOUBLE NOT NULL,
    nace_scope VARCHAR,
    source_id VARCHAR NOT NULL,
    dataset_id VARCHAR NOT NULL,
    retrieved_at TIMESTAMP NOT NULL,
    source_updated_at VARCHAR,
    PRIMARY KEY (country_iso3, period, isco08, source_id)
);

CREATE TABLE IF NOT EXISTS labour_occupation_outlook (
    country_iso3 VARCHAR NOT NULL,
    period INTEGER NOT NULL,
    isco08 VARCHAR NOT NULL,
    isco_level INTEGER NOT NULL,
    occupation_label VARCHAR,
    scenario VARCHAR NOT NULL,
    employment_level_thousands DOUBLE,
    employment_growth_pct DOUBLE,
    source_id VARCHAR NOT NULL,
    dataset_id VARCHAR NOT NULL,
    release_version VARCHAR NOT NULL,
    retrieved_at TIMESTAMP NOT NULL,
    source_updated_at VARCHAR,
    PRIMARY KEY (
        country_iso3, period, isco08, scenario, source_id, release_version
    )
);

CREATE TABLE IF NOT EXISTS labour_job_transitions (
    country_iso3 VARCHAR NOT NULL,
    period INTEGER NOT NULL,
    age_group VARCHAR NOT NULL,
    duration_group VARCHAR NOT NULL,
    probability_pct DOUBLE NOT NULL,
    source_id VARCHAR NOT NULL,
    dataset_id VARCHAR NOT NULL,
    retrieved_at TIMESTAMP NOT NULL,
    source_updated_at VARCHAR,
    PRIMARY KEY (
        country_iso3, period, age_group, duration_group, source_id
    )
);

CREATE TABLE IF NOT EXISTS subnational_observations (
    geo_code VARCHAR NOT NULL,
    geo_level VARCHAR NOT NULL,
    indicator_id VARCHAR NOT NULL,
    period INTEGER NOT NULL,
    value DOUBLE NOT NULL,
    unit VARCHAR,
    source_id VARCHAR NOT NULL,
    dataset_id VARCHAR NOT NULL,
    retrieved_at TIMESTAMP NOT NULL,
    source_updated_at VARCHAR,
    PRIMARY KEY (geo_code, indicator_id, period, source_id)
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


def upsert_labour_net_earnings_reference(rows: list[dict]) -> int:
    if not rows:
        return 0

    con = duckdb.connect(str(settings.duckdb_path))
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO labour_net_earnings_reference
            (
                country_iso3, period, earnings_case, annual_net_eur,
                source_id, dataset_id, retrieved_at, source_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                [
                    row["country_iso3"],
                    row["period"],
                    row["earnings_case"],
                    row["annual_net_eur"],
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


def latest_labour_net_earnings_reference(
    country_iso3: str,
    earnings_case: str = "P1_NCH_AW100",
) -> dict | None:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            SELECT
                country_iso3, period, earnings_case, annual_net_eur,
                source_id, dataset_id, retrieved_at, source_updated_at
            FROM labour_net_earnings_reference
            WHERE country_iso3 = ?
              AND earnings_case = ?
            ORDER BY period DESC, source_id ASC
            LIMIT 1
            """,
            [country_iso3.upper(), earnings_case],
        )
        row = result.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in result.description]
        return dict(zip(columns, row))
    finally:
        con.close()


def upsert_labour_job_vacancy_rates(rows: list[dict]) -> int:
    if not rows:
        return 0

    con = duckdb.connect(str(settings.duckdb_path))
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO labour_job_vacancy_rates
            (
                country_iso3, period, isco08, vacancy_rate_pct,
                nace_scope, source_id, dataset_id,
                retrieved_at, source_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                [
                    row["country_iso3"],
                    row["period"],
                    row["isco08"],
                    row["vacancy_rate_pct"],
                    row.get("nace_scope"),
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


def latest_labour_job_vacancy_rate(
    country_iso3: str,
    isco08: str,
) -> dict | None:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            SELECT
                country_iso3, period, isco08, vacancy_rate_pct,
                nace_scope, source_id, dataset_id,
                retrieved_at, source_updated_at
            FROM labour_job_vacancy_rates
            WHERE country_iso3 = ?
              AND isco08 = ?
            ORDER BY period DESC, source_id ASC
            LIMIT 1
            """,
            [country_iso3.upper(), isco08.upper()],
        )
        row = result.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in result.description]
        return dict(zip(columns, row))
    finally:
        con.close()




def upsert_labour_occupation_outlook(rows: list[dict]) -> int:
    if not rows:
        return 0

    con = duckdb.connect(str(settings.duckdb_path))
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO labour_occupation_outlook
            (
                country_iso3, period, isco08, isco_level, occupation_label,
                scenario, employment_level_thousands, employment_growth_pct,
                source_id, dataset_id, release_version, retrieved_at,
                source_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                [
                    row["country_iso3"],
                    row["period"],
                    row["isco08"],
                    row["isco_level"],
                    row.get("occupation_label"),
                    row["scenario"],
                    row.get("employment_level_thousands"),
                    row.get("employment_growth_pct"),
                    row["source_id"],
                    row["dataset_id"],
                    row["release_version"],
                    row["retrieved_at"],
                    row.get("source_updated_at"),
                ]
                for row in rows
            ],
        )
        return len(rows)
    finally:
        con.close()


def latest_labour_occupation_outlook(
    country_iso3: str,
    isco08: str,
    scenario: str = "Aligned_forecast_Ameco",
) -> list[dict]:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        table_exists = con.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = 'labour_occupation_outlook'
            """
        ).fetchone()[0]

        if not table_exists:
            return []

        result = con.execute(
            """
            SELECT
                country_iso3, period, isco08, isco_level, occupation_label,
                scenario, employment_level_thousands, employment_growth_pct,
                source_id, dataset_id, release_version, retrieved_at,
                source_updated_at
            FROM labour_occupation_outlook
            WHERE country_iso3 = ?
              AND isco08 = ?
              AND scenario = ?
            ORDER BY period, release_version DESC
            """,
            [country_iso3.upper(), str(isco08), scenario],
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()

def labour_occupation_outlook_status() -> dict:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        table_exists = con.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = 'labour_occupation_outlook'
            """
        ).fetchone()[0]

        if not table_exists:
            return {
                "available": False,
                "row_count": 0,
                "country_count": 0,
                "countries": [],
                "periods": [],
                "isco_levels": [],
                "release_versions": [],
                "latest_retrieved_at": None,
            }

        row = con.execute(
            """
            SELECT
                COUNT(*) AS row_count,
                COUNT(DISTINCT country_iso3) AS country_count,
                MAX(retrieved_at) AS latest_retrieved_at
            FROM labour_occupation_outlook
            """
        ).fetchone()
        countries = [
            value[0] for value in con.execute(
                "SELECT DISTINCT country_iso3 FROM labour_occupation_outlook ORDER BY country_iso3"
            ).fetchall()
        ]
        periods = [
            value[0] for value in con.execute(
                "SELECT DISTINCT period FROM labour_occupation_outlook ORDER BY period"
            ).fetchall()
        ]
        isco_levels = [
            value[0] for value in con.execute(
                "SELECT DISTINCT isco_level FROM labour_occupation_outlook ORDER BY isco_level"
            ).fetchall()
        ]
        releases = [
            value[0] for value in con.execute(
                "SELECT DISTINCT release_version FROM labour_occupation_outlook ORDER BY release_version"
            ).fetchall()
        ]
        return {
            "available": bool(row[0]),
            "row_count": row[0],
            "country_count": row[1],
            "countries": countries,
            "periods": periods,
            "isco_levels": isco_levels,
            "release_versions": releases,
            "latest_retrieved_at": row[2],
        }
    finally:
        con.close()


def upsert_labour_job_transitions(rows: list[dict]) -> int:
    if not rows:
        return 0

    con = duckdb.connect(str(settings.duckdb_path))
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO labour_job_transitions
            (
                country_iso3, period, age_group, duration_group,
                probability_pct, source_id, dataset_id,
                retrieved_at, source_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                [
                    row["country_iso3"],
                    row["period"],
                    row["age_group"],
                    row["duration_group"],
                    row["probability_pct"],
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


def latest_labour_job_transition(
    country_iso3: str,
    age_group: str = "Y15-74",
    duration_group: str = "TOTAL",
) -> dict | None:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            SELECT
                country_iso3, period, age_group, duration_group,
                probability_pct, source_id, dataset_id,
                retrieved_at, source_updated_at
            FROM labour_job_transitions
            WHERE country_iso3 = ?
              AND age_group = ?
              AND duration_group = ?
            ORDER BY period DESC, source_id ASC
            LIMIT 1
            """,
            [country_iso3.upper(), age_group, duration_group],
        )
        row = result.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in result.description]
        return dict(zip(columns, row))
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


def country_indicator_series(
    country_iso3: str,
    max_points: int = 8,
) -> list[dict]:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            WITH ranked_source AS (
                SELECT
                    o.country_iso3,
                    o.indicator_id,
                    i.name,
                    i.dimension,
                    o.period,
                    o.value,
                    o.unit,
                    o.source_id,
                    s.priority,
                    ROW_NUMBER() OVER (
                        PARTITION BY o.indicator_id, o.period
                        ORDER BY s.priority ASC, o.source_id ASC
                    ) AS source_rank
                FROM observations o
                JOIN indicators i USING (indicator_id)
                JOIN sources s USING (source_id)
                WHERE o.country_iso3 = ?
                  AND o.observation_type = 'observed'
            ),
            preferred AS (
                SELECT *
                FROM ranked_source
                WHERE source_rank = 1
            ),
            recent AS (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY indicator_id
                        ORDER BY period DESC
                    ) AS point_rank
                FROM preferred
            )
            SELECT
                country_iso3,
                indicator_id,
                name,
                dimension,
                period,
                value,
                unit,
                source_id
            FROM recent
            WHERE point_rank <= ?
            ORDER BY indicator_id, period
            """,
            [country_iso3.upper(), max_points],
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


def analytical_evidence_status() -> dict:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        observation_rows = con.execute(
            """
            SELECT
                c.iso3 AS country_iso3,
                COUNT(o.indicator_id) FILTER (
                    WHERE o.observation_type = 'observed'
                ) AS observed_rows,
                COUNT(DISTINCT o.indicator_id) FILTER (
                    WHERE o.observation_type = 'observed'
                ) AS observed_indicators,
                MAX(o.period) FILTER (
                    WHERE o.observation_type = 'observed'
                ) AS latest_observed_period,
                MAX(o.retrieved_at) AS latest_retrieved_at,
                COUNT(o.indicator_id) FILTER (
                    WHERE o.observation_type = 'official_forecast'
                ) AS official_forecast_rows,
                COUNT(DISTINCT o.source_id) AS source_count,
                LIST(DISTINCT o.source_id) FILTER (
                    WHERE o.source_id IS NOT NULL
                ) AS source_ids
            FROM countries c
            LEFT JOIN observations o
              ON o.country_iso3 = c.iso3
            GROUP BY c.iso3
            ORDER BY c.iso3
            """
        ).fetchall()

        provider_freshness_rows = con.execute(
            """
            SELECT
                country_iso3,
                source_id,
                MAX(retrieved_at) AS latest_retrieved_at
            FROM observations
            GROUP BY country_iso3, source_id
            ORDER BY country_iso3, source_id
            """
        ).fetchall()

        earnings_rows = con.execute(
            """
            SELECT
                c.iso3 AS country_iso3,
                COUNT(e.isco08) AS row_count,
                COUNT(DISTINCT e.isco08) AS isco_group_count,
                MAX(e.period) AS latest_period,
                MAX(e.retrieved_at) AS latest_retrieved_at
            FROM countries c
            LEFT JOIN labour_earnings e
              ON e.country_iso3 = c.iso3
            GROUP BY c.iso3
            ORDER BY c.iso3
            """
        ).fetchall()

        net_earnings_rows = con.execute(
            """
            SELECT
                c.iso3 AS country_iso3,
                COUNT(n.earnings_case) AS row_count,
                MAX(n.period) AS latest_period,
                MAX(n.retrieved_at) AS latest_retrieved_at
            FROM countries c
            LEFT JOIN labour_net_earnings_reference n
              ON n.country_iso3 = c.iso3
            GROUP BY c.iso3
            ORDER BY c.iso3
            """
        ).fetchall()

        job_vacancy_rows = con.execute(
            """
            SELECT
                c.iso3 AS country_iso3,
                COUNT(v.isco08) AS row_count,
                COUNT(DISTINCT v.isco08) AS isco_group_count,
                MAX(v.period) AS latest_period,
                MAX(v.retrieved_at) AS latest_retrieved_at
            FROM countries c
            LEFT JOIN labour_job_vacancy_rates v
              ON v.country_iso3 = c.iso3
            GROUP BY c.iso3
            ORDER BY c.iso3
            """
        ).fetchall()

        job_transition_rows = con.execute(
            """
            SELECT
                c.iso3 AS country_iso3,
                COUNT(j.age_group) AS row_count,
                COUNT(DISTINCT j.age_group) AS age_group_count,
                MAX(j.period) AS latest_period,
                MAX(j.retrieved_at) AS latest_retrieved_at
            FROM countries c
            LEFT JOIN labour_job_transitions j
              ON j.country_iso3 = c.iso3
            GROUP BY c.iso3
            ORDER BY c.iso3
            """
        ).fetchall()

        observation_columns = [
            "country_iso3",
            "observed_rows",
            "observed_indicators",
            "latest_observed_period",
            "latest_retrieved_at",
            "official_forecast_rows",
            "source_count",
            "source_ids",
        ]
        earnings_columns = [
            "country_iso3",
            "row_count",
            "isco_group_count",
            "latest_period",
            "latest_retrieved_at",
        ]

        net_earnings_columns = [
            "country_iso3",
            "row_count",
            "latest_period",
            "latest_retrieved_at",
        ]

        job_vacancy_columns = [
            "country_iso3",
            "row_count",
            "isco_group_count",
            "latest_period",
            "latest_retrieved_at",
        ]

        job_transition_columns = [
            "country_iso3",
            "row_count",
            "age_group_count",
            "latest_period",
            "latest_retrieved_at",
        ]

        provider_freshness = {}
        for country_iso3, source_id, latest_retrieved_at in provider_freshness_rows:
            provider_freshness.setdefault(country_iso3, {})[source_id] = latest_retrieved_at

        observations = {}
        for row in observation_rows:
            item = dict(zip(observation_columns, row))
            item["source_ids"] = sorted(item.get("source_ids") or [])
            item["provider_retrieved_at"] = provider_freshness.get(row[0], {})
            observations[row[0]] = item
        earnings = {
            row[0]: dict(zip(earnings_columns, row))
            for row in earnings_rows
        }
        net_earnings = {
            row[0]: dict(zip(net_earnings_columns, row))
            for row in net_earnings_rows
        }
        job_vacancies = {
            row[0]: dict(zip(job_vacancy_columns, row))
            for row in job_vacancy_rows
        }
        job_transitions = {
            row[0]: dict(zip(job_transition_columns, row))
            for row in job_transition_rows
        }

        return {
            "countries": [
                {
                    **observations[country_iso3],
                    "labour_earnings": earnings[country_iso3],
                    "net_earnings": net_earnings[country_iso3],
                    "job_vacancies": job_vacancies[country_iso3],
                    "job_transitions": job_transitions[country_iso3],
                }
                for country_iso3 in sorted(observations)
            ]
        }
    finally:
        con.close()


def upsert_subnational_observations(rows: list[dict]) -> int:
    if not rows:
        return 0

    con = duckdb.connect(str(settings.duckdb_path))
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO subnational_observations
            (
                geo_code, geo_level, indicator_id, period, value, unit,
                source_id, dataset_id, retrieved_at, source_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                [
                    row["geo_code"].upper(),
                    row["geo_level"],
                    row["indicator_id"],
                    row["period"],
                    row["value"],
                    row.get("unit"),
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


def latest_subnational_observations(geo_code: str) -> list[dict]:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        result = con.execute(
            """
            WITH ranked AS (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY indicator_id
                        ORDER BY period DESC, source_id ASC
                    ) AS rn
                FROM subnational_observations
                WHERE geo_code = ?
            )
            SELECT
                geo_code, geo_level, indicator_id, period, value, unit,
                source_id, dataset_id, retrieved_at, source_updated_at
            FROM ranked
            WHERE rn = 1
            ORDER BY indicator_id
            """,
            [geo_code.upper()],
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]
    finally:
        con.close()


def subnational_storage_status() -> dict:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        row = con.execute(
            """
            SELECT
                COUNT(*) AS observation_count,
                COUNT(DISTINCT geo_code) AS geography_count,
                COUNT(DISTINCT CASE WHEN geo_level = 'nuts2' THEN geo_code END) AS nuts2_count,
                COUNT(DISTINCT CASE WHEN geo_level = 'city' THEN geo_code END) AS city_count
            FROM subnational_observations
            """
        ).fetchone()
        return {
            "observation_count": int(row[0]),
            "geography_count": int(row[1]),
            "nuts2_count": int(row[2]),
            "city_count": int(row[3]),
        }
    finally:
        con.close()
