"""Read-only GR-2 evidence: export exact pilot observation identities.

The output contains no values. It intentionally does not assert that a matching
code proves a reference-year observation's statistical boundary vintage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
from app.core.config import settings
from app.services.ranking_eligibility import PILOT_CONTRACTS


def build_report(db_path: Path, indicator_id: str) -> dict:
    contract = PILOT_CONTRACTS[indicator_id]
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = connection.execute(
            """
            SELECT g.geo_id, g.country_iso3, g.source_geo_code, g.name,
                   g.geography_system, g.geo_level, s.period, s.unit,
                   s.source_id, s.dataset_id, s.source_updated_at,
                   COUNT(*) AS rows
            FROM geography_registry g
            JOIN subnational_observations s
              ON s.geography_system = g.geography_system
             AND s.geo_code = g.source_geo_code
             AND LOWER(s.geo_level) = LOWER(g.geo_level)
            WHERE s.indicator_id = ? AND s.period = ?
            GROUP BY ALL ORDER BY g.country_iso3, g.source_geo_code
            """,
            [contract.indicator_id, contract.period],
        ).fetchall()
    finally:
        connection.close()
    columns = ("geo_id", "country_iso3", "source_geo_code", "name",
               "geography_system", "geo_level", "period", "unit",
               "source_id", "dataset_id", "source_updated_at", "stored_rows")
    return {
        "indicator_id": indicator_id,
        "reference_period": contract.period,
        "status": "observation_identity_inventory_not_vintage_certification",
        "observation_count": sum(row[-1] for row in rows),
        "locations": [
            dict(zip(columns, [str(value) if value is not None else None
                               for value in row]))
            for row in rows
        ],
        "verification_required": [
            "Confirm authoritative NUTS 2024 membership of each geo code",
            "Confirm source dataset applies NUTS 2024 to this observation cohort",
            "Verify source dimensions/age group/unit/status and measurement semantics",
            "Confirm no conflicting rows and explain exclusions",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--indicator", choices=sorted(PILOT_CONTRACTS),
                        default="regional_unemployment_rate")
    args = parser.parse_args()
    if args.output.suffix.lower() != ".json":
        parser.error("Use a JSON output file")
    report = build_report(settings.duckdb_path, args.indicator)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"output": str(args.output),
                      "locations": len(report["locations"]),
                      "status": report["status"]}))


if __name__ == "__main__":
    main()
