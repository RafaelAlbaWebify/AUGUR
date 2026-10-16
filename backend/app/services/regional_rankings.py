"""Read-only GR-2 ranking service, rejecting unverified boundary vintages."""
from __future__ import annotations

from pathlib import Path
import duckdb
from app.core.config import settings
from app.services.ranking_eligibility import PILOT_CONTRACTS, RankingCandidate, ordered_eligible
from app.services.ranking_provider_metadata import check_provider_metadata


def regional_rankings(indicator_id: str, countries=("ESP", "PRT", "IRL"), *,
                      descending=False, limit=50, offset=0,
                      db_path: Path | None = None, verified_geo_ids=frozenset()):
    contract = PILOT_CONTRACTS.get(indicator_id)
    if contract is None:
        raise ValueError("Unsupported indicator")
    codes = tuple(sorted(set(c.upper() for c in countries)))
    if not codes or any(len(c) != 3 or not c.isalpha() for c in codes):
        raise ValueError("Invalid country selection")
    if not 1 <= limit <= 200 or offset < 0:
        raise ValueError("Invalid pagination")
    marks = ",".join("?" for _ in codes)
    con = duckdb.connect(str(db_path or settings.duckdb_path), read_only=True)
    try:
        available_columns = {row[1] for row in con.execute("PRAGMA table_info('subnational_observations')").fetchall()}
        dimensions_expr = "s.response_dimensions_json" if "response_dimensions_json" in available_columns else "NULL"
        status_expr = "s.source_observation_status" if "source_observation_status" in available_columns else "NULL"
        rows = con.execute(f"""
            SELECT g.geo_id, g.country_iso3, g.name, s.indicator_id, s.geo_level,
                   s.geography_system, s.unit, s.source_id, s.dataset_id,
                   s.period, s.value, {dimensions_expr}, {status_expr}, s.geo_code
            FROM geography_registry g JOIN subnational_observations s
              ON g.geography_system=s.geography_system
             AND g.source_geo_code=s.geo_code
             AND LOWER(g.geo_level)=LOWER(s.geo_level)
            WHERE g.country_iso3 IN ({marks}) AND s.indicator_id=? AND s.period=?
            ORDER BY g.geo_id
        """, [*codes, indicator_id, contract.period]).fetchall()
    finally:
        con.close()
    labels = {}
    candidates = []
    metadata_rejections = {}
    for geo_id, country, name, indicator, level, system, unit, source, dataset, period, value, dimensions, status, source_geo_code in rows:
        labels[geo_id] = (country, name)
        metadata_rejections.setdefault(geo_id, []).extend(check_provider_metadata(
            dimensions, status, geo_code=source_geo_code, period=period
        ))
        candidates.append(RankingCandidate(
            geo_id=geo_id, indicator_id=indicator, geo_level=level,
            geography_system=system, unit=unit, source_id=source,
            dataset_id=dataset, period=period, value=float(value),
            boundary_verified=geo_id in verified_geo_ids,
        ))
    ranked, exclusions = ordered_eligible(candidates, contract, descending=descending)
    metadata_counts = {}
    for reasons in metadata_rejections.values():
        for reason in reasons:
            metadata_counts[reason] = metadata_counts.get(reason, 0) + 1
    ranked = [item for item in ranked if not metadata_rejections.get(item.geo_id)]
    page = ranked[offset:offset + limit]
    return {
        "status": "ready" if ranked else ("blocked_unverified_evidence" if rows else "no_observations"),
        "scope": "locally_registered_only",
        "indicator_id": indicator_id, "period": contract.period,
        "countries": list(codes), "observed_rows": len(rows),
        "eligible_total": len(ranked), "excluded_reasons": exclusions,
        "provider_metadata_issues": dict(sorted(metadata_counts.items())),
        "limit": limit, "offset": offset,
        "has_more": offset + limit < len(ranked),
        "items": [
            {"rank": offset + i + 1, "geo_id": x.geo_id,
             "country_iso3": labels[x.geo_id][0], "name": labels[x.geo_id][1],
             "value": x.value, "unit": x.unit, "period": x.period,
             "source_id": x.source_id, "dataset_id": x.dataset_id}
            for i, x in enumerate(page)
        ],
        "warning": "NUTS_2024 registry membership does not independently verify historical observation boundary vintage.",
    }
