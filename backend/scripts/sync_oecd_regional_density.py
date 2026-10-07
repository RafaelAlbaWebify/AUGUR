from __future__ import annotations

import argparse
import json

from app.db.analytics import (
    country_record,
    country_registry,
    geography_coverage_status,
)
from app.db.bootstrap import initialize_datastores
from app.ingestion.oecd_regional import OECDRegionalAdapter
from app.ingestion.world_bank import WorldBankAdapter


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize OECD TL2/TL3 population-density evidence."
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        help=(
            "Optional ISO3 countries. Missing countries are registered from "
            "World Bank metadata before the OECD sync."
        ),
    )
    parser.add_argument(
        "--key",
        default="all",
        help="Optional OECD SDMX key. Default: all",
    )
    parser.add_argument("--start-year", type=int, default=2021)
    parser.add_argument("--end-year", type=int)
    args = parser.parse_args()

    initialize_datastores()

    if args.countries:
        requested = {
            value.upper()
            for value in args.countries
        }
        world_bank = WorldBankAdapter(timeout_seconds=90, max_retries=3)
        try:
            for code in sorted(requested):
                if country_record(code) is None:
                    world_bank.ensure_country_registered(code)
        finally:
            world_bank.close()

        target_countries = {
            code
            for code in requested
            if (
                (country_record(code) or {}).get("oecd_member")
                and not (country_record(code) or {}).get("eu_member")
            )
        }
    else:
        target_countries = {
            country["iso3"]
            for country in country_registry()
            if country.get("oecd_member")
            and not country.get("eu_member")
        }

    if not target_countries:
        print(json.dumps({
            "source_id": "OECD",
            "dataset_id": "DSD_REG_DEMO@DF_DENSITY",
            "status": "no_registered_non_eu_oecd_countries",
            "rows": 0,
        }, indent=2))
        return 0

    adapter = OECDRegionalAdapter(
        timeout_seconds=180,
        max_retries=3,
    )
    try:
        result = adapter.sync_density(
            allowed_country_iso3=target_countries,
            start_year=args.start_year,
            end_year=args.end_year,
            key=args.key,
        )
    finally:
        adapter.close()

    payload = {
        **result,
        "target_country_count": len(target_countries),
        "target_countries": sorted(target_countries),
        "geography_coverage": geography_coverage_status(),
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if result["rows"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
