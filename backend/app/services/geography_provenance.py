"""Read-only provenance audit: registered geographies and their actual evidence.

No boundary-era inference: a NUTS_2024 label is not proof that every
stored code is valid in the 2024 official NUTS release.
"""
from __future__ import annotations

import duckdb
from app.core.config import settings


def geography_provenance(country_iso3: str | None = None) -> dict:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        records = con.execute(
            """
            SELECT g.country_iso3, g.geo_id, g.source_geo_code, g.name,
                   g.geography_system, g.geo_level, g.source_id,
                   g.parent_geo_id, COUNT(DISTINCT s.indicator_id) AS indicators,
                   COUNT(DISTINCT s.period) AS years,
                   MIN(s.period) AS first_period,
                   MAX(s.period) AS last_period,
                   LIST(DISTINCT s.indicator_id ORDER BY s.indicator_id)
                     FILTER (WHERE s.indicator_id IS NOT NULL) AS indicator_ids,
                   LIST(DISTINCT s.source_id ORDER BY s.source_id)
                     FILTER (WHERE s.source_id IS NOT NULL) AS evidence_source_ids,
                   LIST(DISTINCT s.dataset_id ORDER BY s.dataset_id)
                     FILTER (WHERE s.dataset_id IS NOT NULL) AS dataset_ids
            FROM geography_registry g
            LEFT JOIN subnational_observations s
              ON s.geography_system = g.geography_system
             AND s.geo_code = g.source_geo_code
             AND LOWER(s.geo_level) = LOWER(g.geo_level)
            WHERE (? IS NULL OR UPPER(g.country_iso3) = ?)
            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
            ORDER BY 1, 5, 6, 3
            """,
            [country_iso3.upper() if country_iso3 else None] * 2,
        ).fetchall()
    finally:
        con.close()
    items = []
    for country, geo_id, code, name, system, level, source, parent, count, years, first, last, indicators, evidence_sources, datasets in records:
        items.append({
            "country_iso3": country,
            "geo_id": geo_id,
            "source_geo_code": code,
            "name": name,
            "geography_system": system,
            "geo_level": level,
            "registry_source_id": source,
            "parent_geo_id": parent,
            "observed_indicator_count": int(count),
            "observed_period_count": int(years),
            "first_observed_period": first,
            "last_observed_period": last,
            "indicator_ids": list(indicators or []),
            "evidence_source_ids": list(evidence_sources or []),
            "dataset_ids": list(datasets or []),
            "has_evidence": bool(count),
            "boundary_version_verified": False,
        })
    return {
        "status": "observed_local_registry_only",
        "warning": (
            "This report lists stored geography identities and imported evidence. "
            "It does not certify NUTS code validity, current boundary versions, "
            "provider completeness, statistical comparability or values."
        ),
        "registered_geography_count": len(items),
        "items": items,
    }
