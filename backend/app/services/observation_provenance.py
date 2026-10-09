"""Read-only audit of actual regional observation source/unit/period evidence.

This is an inventory of stored observations, not a provider completeness claim.
"""
from __future__ import annotations

import duckdb
from app.core.config import settings


def observation_provenance(country_iso3: str | None = None) -> dict:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        existing = {
            row[0] for row in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
        }
        missing = {"geography_registry", "subnational_observations"} - existing
        if missing:
            raise RuntimeError(
                "AUGUR analytical schema is not initialized; missing "
                + ", ".join(sorted(missing))
                + ". Initialize datastores explicitly before exporting."
            )
        rows = con.execute("""
            WITH registered AS (
                SELECT DISTINCT country_iso3, geography_system, geo_level,
                       source_geo_code
                FROM geography_registry
                WHERE (? IS NULL OR UPPER(country_iso3) = ?)
            )
            SELECT r.country_iso3, r.geography_system, r.geo_level,
                   s.indicator_id, s.source_id, s.dataset_id, s.unit,
                   COUNT(*) AS observation_rows,
                   COUNT(DISTINCT s.geo_code) AS observed_geographies,
                   COUNT(DISTINCT s.period) AS distinct_periods,
                   MIN(s.period) AS first_period,
                   MAX(s.period) AS last_period,
                   MIN(s.retrieved_at) AS first_ingestion,
                   MAX(s.retrieved_at) AS last_ingestion
            FROM registered r
            JOIN subnational_observations s
              ON s.geography_system = r.geography_system
             AND s.geo_code = r.source_geo_code
             AND LOWER(s.geo_level) = LOWER(r.geo_level)
            GROUP BY 1,2,3,4,5,6,7
            ORDER BY 1,2,3,4,5,6,7
        """, [country_iso3.upper() if country_iso3 else None] * 2).fetchall()
        unregistered = con.execute("""
            SELECT s.geography_system, s.geo_level, s.geo_code,
                   COUNT(*) AS observation_rows
            FROM subnational_observations s
            LEFT JOIN geography_registry g
              ON g.geography_system = s.geography_system
             AND g.source_geo_code = s.geo_code
             AND LOWER(g.geo_level) = LOWER(s.geo_level)
            WHERE g.geo_id IS NULL
            GROUP BY 1,2,3 ORDER BY 1,2,3
        """).fetchall()
    finally:
        con.close()
    items = [
        dict(
            country_iso3=country, geography_system=system, geo_level=level,
            indicator_id=indicator, source_id=source, dataset_id=dataset,
            unit=unit, observation_rows=int(count),
            observed_geographies=int(geos), distinct_periods=int(periods),
            first_period=first, last_period=last,
            first_ingestion=ingested_min.isoformat() if ingested_min else None,
            last_ingestion=ingested_max.isoformat() if ingested_max else None,
        )
        for country, system, level, indicator, source, dataset, unit,
        count, geos, periods, first, last, ingested_min, ingested_max in rows
    ]
    return {
        "scope": "locally_stored_registered_observations",
        "warning": "No inference about official provider coverage, source comparability, or current boundaries. Unit and dataset are kept separate; no imputation.",
        "row_count": len(items),
        "items": items,
        "unregistered_observations": [
            {"geography_system": system, "geo_level": level,
             "geo_code": code, "observation_rows": int(count)}
            for system, level, code, count in unregistered
        ],
        "unregistered_scope": "global_store_not_filtered_by_country",
    }
