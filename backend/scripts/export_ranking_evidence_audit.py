"""GR-0: read-only actual observation contract inventory for geographic rankings.

Execute from backend/: python -m scripts.export_ranking_evidence_audit
  --output ../exports/ranking_evidence_audit.json --countries ESP PRT IRL
The output contains aggregated counts and provenance only, not individual values.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
from app.core.config import settings


def audit(db_path: Path, countries: list[str]) -> dict:
    codes = sorted(set(code.strip().upper() for code in countries))
    if not codes or any(len(code) != 3 or not code.isalpha() for code in codes):
        raise ValueError("Supply ISO3 country codes")
    placeholders = ",".join("?" for _ in codes)
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        national = con.execute(f"""
            SELECT country_iso3, indicator_id, period, unit,
                   source_id, dataset_id, observation_type,
                   COUNT(*) AS stored_rows,
                   COUNT(DISTINCT country_iso3) AS observed_geographies
            FROM observations
            WHERE country_iso3 IN ({placeholders})
            GROUP BY 1,2,3,4,5,6,7 ORDER BY 2,3,1,5
        """, codes).fetchall()
        regional = con.execute(f"""
            WITH registered AS (
                SELECT DISTINCT country_iso3, geography_system, LOWER(geo_level) AS geo_level,
                       source_geo_code
                FROM geography_registry WHERE country_iso3 IN ({placeholders})
            )
            SELECT g.country_iso3, s.geography_system, LOWER(s.geo_level) AS geo_level,
                   s.indicator_id, s.period, s.unit, s.source_id, s.dataset_id,
                   COUNT(*) AS stored_rows, COUNT(DISTINCT s.geo_code) AS observed_geographies
            FROM subnational_observations s
            JOIN registered g ON s.geography_system = g.geography_system
                AND LOWER(s.geo_level) = g.geo_level AND s.geo_code = g.source_geo_code
            GROUP BY 1,2,3,4,5,6,7,8 ORDER BY 4,5,1,2,3
        """, codes).fetchall()
        registry = con.execute(f"""
            SELECT country_iso3, geography_system, LOWER(geo_level) AS geo_level,
                   COUNT(DISTINCT source_geo_code) AS registered_geographies
            FROM geography_registry WHERE country_iso3 IN ({placeholders})
            GROUP BY 1,2,3 ORDER BY 1,2,3
        """, codes).fetchall()
    finally:
        con.close()
    national_columns = ("country_iso3", "indicator_id", "period", "unit", "source_id",
                        "dataset_id", "observation_type", "stored_rows", "observed_geographies")
    regional_columns = ("country_iso3", "geography_system", "geo_level", "indicator_id",
                        "period", "unit", "source_id", "dataset_id", "stored_rows", "observed_geographies")
    reg_columns = ("country_iso3", "geography_system", "geo_level", "registered_geographies")
    return {
        "scope": "local_registered_evidence_only_not_worldwide_provider_coverage",
        "countries": codes,
        "warning": "Geography systems are not proven boundary-equivalent; matching year/unit/source does not by itself certify semantic comparability. City and FUA levels are distinct. Stored observations can be out-of-date. Null country attribution or unregistered geographies are not silently assigned.",
        "national_observations": [dict(zip(national_columns, row)) for row in national],
        "subnational_observations": [dict(zip(regional_columns, row)) for row in regional],
        "registered_geography_groups": [dict(zip(reg_columns, row)) for row in registry],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--countries", nargs="+", default=["ESP", "PRT", "IRL"])
    args = parser.parse_args()
    if args.output.suffix.lower() != ".json":
        parser.error("Output must end in .json")
    result = audit(settings.duckdb_path, args.countries)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "national_groups": len(result["national_observations"]),
                      "subnational_groups": len(result["subnational_observations"])}))


if __name__ == "__main__":
    main()
