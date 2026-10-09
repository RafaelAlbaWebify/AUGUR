"""Read-only export of real locally stored subnational indicator coverage.

Run from backend/: python scripts/export_geography_coverage.py --output exports/coverage.json
No remote fetch, synthetic observations, or write to analytical storage.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from app.services.geography_indicator_coverage import indicator_geography_coverage


def export_coverage(*, output: Path, country: str | None = None,
                    system: str | None = None, level: str | None = None) -> dict:
    result = indicator_geography_coverage(
        country_iso3=country,
        geography_system=system,
        geo_level=level,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".csv":
        fields = [
            "country_iso3", "geography_system", "geo_level", "indicator_id",
            "registered_geographies", "covered_geographies",
            "missing_geographies", "coverage_ratio", "oldest_latest_period",
            "newest_latest_period", "earliest_ingestion_by_geography",
            "most_recent_ingestion", "same_period_coverage",
            "latest_period_distribution",
        ]
        with output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for row in result["items"]:
                writer.writerow({
                    key: json.dumps(row[key], ensure_ascii=False)
                    if isinstance(row.get(key), list) else row.get(key)
                    for key in fields
                })
    elif output.suffix.lower() == ".json":
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        raise ValueError("Only .json and .csv exports are supported")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--country", help="ISO3, e.g. ESP")
    parser.add_argument("--system", help="Exact registered geography system")
    parser.add_argument("--level", help="Exact geography level")
    args = parser.parse_args()
    result = export_coverage(
        output=args.output,
        country=args.country,
        system=args.system,
        level=args.level,
    )
    print(json.dumps({
        "output": str(args.output),
        "indicator_count": result["indicator_count"],
        "groups_without_observations": len(result["groups_without_observations"]),
        "denominator": result["denominator"],
    }, indent=2))


if __name__ == "__main__":
    main()
