"""Observed indicator coverage relative to registered subnational geographies."""
from __future__ import annotations

import duckdb
from app.core.config import settings


def indicator_geography_coverage(
    country_iso3: str | None = None,
    geography_system: str | None = None,
    geo_level: str | None = None,
) -> dict:
    filters = []
    params: list[str] = []
    for field, value in (
        ("g.country_iso3", country_iso3),
        ("g.geography_system", geography_system),
        ("g.geo_level", geo_level),
    ):
        if value:
            filters.append(f"UPPER({field}) = ?")
            params.append(value.upper())
    where = "WHERE " + " AND ".join(filters) if filters else ""

    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        rows = con.execute(f"""
            WITH registered AS (
                SELECT DISTINCT g.country_iso3, g.geography_system,
                    g.geo_level, g.source_geo_code
                FROM geography_registry g
                {where}
            ),
            denominators AS (
                SELECT country_iso3, geography_system, geo_level,
                    COUNT(*) AS registered_geographies
                FROM registered GROUP BY 1, 2, 3
            ),
            latest AS (
                SELECT r.country_iso3, r.geography_system, r.geo_level,
                    r.source_geo_code, s.indicator_id,
                    MAX(s.period) AS latest_period,
                    MAX(s.retrieved_at) AS latest_retrieved_at
                FROM registered r
                JOIN subnational_observations s
                  ON s.geography_system = r.geography_system
                 AND s.geo_code = r.source_geo_code
                 AND LOWER(s.geo_level) = LOWER(r.geo_level)
                GROUP BY 1, 2, 3, 4, 5
            )
            SELECT d.country_iso3, d.geography_system, d.geo_level,
                d.registered_geographies, l.indicator_id,
                COUNT(l.source_geo_code) AS covered_geographies,
                MIN(l.latest_period) AS oldest_latest_period,
                MAX(l.latest_period) AS newest_latest_period,
                MIN(l.latest_retrieved_at) AS earliest_latest_retrieval,
                MAX(l.latest_retrieved_at) AS latest_retrieval,
                LIST(l.latest_period ORDER BY l.latest_period)
                    FILTER (WHERE l.latest_period IS NOT NULL) AS geography_latest_periods
            FROM denominators d
            LEFT JOIN latest l
              ON l.country_iso3 IS NOT DISTINCT FROM d.country_iso3
             AND l.geography_system = d.geography_system
             AND l.geo_level = d.geo_level
            GROUP BY 1, 2, 3, 4, 5 ORDER BY 1, 2, 3, 5
        """, params).fetchall()
    finally:
        con.close()

    groups = [
        {
            "country_iso3": country,
            "geography_system": system,
            "geo_level": level,
            "registered_geographies": int(total),
            "has_observed_indicators": indicator is not None,
        }
        for country, system, level, total, indicator, *_ in rows
        if indicator is None
    ]
    items = []
    for country, system, level, total, indicator, observed, oldest, newest, earliest_retrieval, latest_retrieval, periods in rows:
        if indicator is None:
            continue
        total, observed = int(total), int(observed)
        ratio = observed / total if total else 0.0
        period_counts: dict[int, int] = {}
        for period in periods or []:
            period_counts[int(period)] = period_counts.get(int(period), 0) + 1
        items.append({
            "country_iso3": country,
            "geography_system": system,
            "geo_level": level,
            "indicator_id": indicator,
            "registered_geographies": total,
            "covered_geographies": observed,
            "missing_geographies": total - observed,
            "coverage_ratio": ratio,
            "oldest_latest_period": oldest,
            "newest_latest_period": newest,
            "latest_period_distribution": [
                {"period": period, "geography_count": count}
                for period, count in sorted(period_counts.items())
            ],
            "earliest_latest_retrieval": earliest_retrieval.isoformat() if earliest_retrieval else None,
            "latest_retrieval": latest_retrieval.isoformat() if latest_retrieval else None,
        })
    return {
        "denominator": "registered_geographies",
        "coverage_classification": "none",
        "warning": (
            "Coverage is relative to registered geographies, not the external "
            "provider universe. Period range does not establish freshness "
            "or cross-geography comparability. The latest-period distribution "
            "reflects each geography\u0027s latest imported observation, not synchronized "
            "common-period availability. Retrieval timestamps indicate "
            "ingestion activity, not source observation freshness."
        ),
        "indicator_count": len(items),
        "groups_without_observations": groups,
        "items": items,
    }
