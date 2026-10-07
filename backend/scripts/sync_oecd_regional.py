from __future__ import annotations

import argparse
import json

from app.db.analytics import (
    country_record,
    country_registry,
    geography_coverage_status,
)
from app.db.bootstrap import initialize_datastores
from app.ingestion.oecd_regional import (
    DENSITY_DEFAULT_KEY,
    POPULATION_DEFAULT_KEY,
    OECDRegionalAdapter,
)
from app.ingestion.world_bank import WorldBankAdapter


def _target_countries(requested: list[str] | None) -> set[str]:
    if requested:
        requested_codes = {value.upper() for value in requested}
        world_bank = WorldBankAdapter(timeout_seconds=90, max_retries=3)
        try:
            for code in sorted(requested_codes):
                if country_record(code) is None:
                    world_bank.ensure_country_registered(code)
        finally:
            world_bank.close()

        return {
            code
            for code in requested_codes
            if (
                (country_record(code) or {}).get("oecd_member")
                and not (country_record(code) or {}).get("eu_member")
            )
        }

    return {
        country["iso3"]
        for country in country_registry()
        if country.get("oecd_member")
        and not country.get("eu_member")
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize OECD non-EU TL2/TL3 regional evidence."
    )
    parser.add_argument("--countries", nargs="+")
    parser.add_argument("--start-year", type=int, default=2021)
    parser.add_argument("--end-year", type=int)
    parser.add_argument(
        "--density-key",
        default=DENSITY_DEFAULT_KEY,
        help="Optional OECD density SDMX key.",
    )
    parser.add_argument(
        "--population-key",
        default=POPULATION_DEFAULT_KEY,
        help="Optional OECD population SDMX key.",
    )
    args = parser.parse_args()

    initialize_datastores()
    targets = _target_countries(args.countries)

    if not targets:
        print(json.dumps({
            "source_id": "OECD",
            "status": "no_registered_non_eu_oecd_countries",
            "rows": 0,
        }, indent=2))
        return 0

    adapter = OECDRegionalAdapter(timeout_seconds=180, max_retries=3)
    try:
        density = adapter.sync_density(
            allowed_country_iso3=targets,
            start_year=args.start_year,
            end_year=args.end_year,
            key=args.density_key,
        )
        population = adapter.sync_population(
            allowed_country_iso3=targets,
            start_year=args.start_year,
            end_year=args.end_year,
            key=args.population_key,
        )
    finally:
        adapter.close()

    total_rows = density["rows"] + population["rows"]
    payload = {
        "source_id": "OECD",
        "target_country_count": len(targets),
        "target_countries": sorted(targets),
        "rows": total_rows,
        "datasets": {
            "density": density,
            "population": population,
        },
        "geography_coverage": geography_coverage_status(),
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if total_rows > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
