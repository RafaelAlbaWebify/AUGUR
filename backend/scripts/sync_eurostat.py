from __future__ import annotations

import argparse

from app.catalog import COUNTRIES
from app.db.bootstrap import initialize_datastores
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_labour import fetch_regional_labour
from app.ingestion.eurostat_regional_sector import fetch_regional_sector_employment
from app.db.analytics import (
    upsert_subnational_observations,
    upsert_regional_sector_employment,
)


DEFAULT_COUNTRIES = [
    country["iso3"]
    for country in COUNTRIES
    if country.get("eu_member")
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize Eurostat data.")
    parser.add_argument(
        "--countries",
        nargs="+",
        default=DEFAULT_COUNTRIES,
        help="ISO3 country codes. Default: all registered EU countries.",
    )
    parser.add_argument(
        "--skip-regional",
        action="store_true",
        help="Skip NUTS2 labour and sector refresh.",
    )
    args = parser.parse_args()

    countries = [value.upper() for value in args.countries]
    registered = {country["iso3"] for country in COUNTRIES}

    unknown = [code for code in countries if code not in registered]
    if unknown:
        raise SystemExit(f"Unsupported countries: {', '.join(unknown)}")

    initialize_datastores()
    adapter = EurostatAdapter(timeout_seconds=90, max_retries=3)

    all_results = {}

    try:
        for country_iso3 in countries:
            print()
            print("=" * 72)
            print(f"AUGUR EUROSTAT SYNC · {country_iso3}")
            print("=" * 72)
            all_results[country_iso3] = adapter.sync_country(country_iso3)
        regional_summary = None
        if not args.skip_regional:
            regional_rows, regional_diagnostics = fetch_regional_labour(adapter)
            sector_rows, sector_diagnostic = fetch_regional_sector_employment(adapter)

            regional_summary = {
                "labour_rows": upsert_subnational_observations(regional_rows),
                "sector_rows": upsert_regional_sector_employment(sector_rows),
                "labour_diagnostics": regional_diagnostics,
                "sector_diagnostic": sector_diagnostic,
            }
    finally:
        adapter.close()

    print()
    print("=" * 72)
    print("AUGUR EUROSTAT SYNC SUMMARY")
    print("=" * 72)

    complete = True

    for country_iso3, result in all_results.items():
        complete = complete and bool(result["complete"])
        print(
            f"{country_iso3}: rows={result['rows']} "
            f"succeeded={len(result['series'])} "
            f"failed={len(result['failures'])} "
            f"complete={result['complete']}"
        )

        for failure in result["failures"]:
            print(
                " -",
                failure["indicator_id"],
                failure["dataset_id"],
                failure["error_type"],
                failure["error"],
            )

    if regional_summary is not None:
        print()
        print(
            "Regional NUTS2: "
            f"labour_rows={regional_summary['labour_rows']} "
            f"sector_rows={regional_summary['sector_rows']}"
        )

    print()
    print("Complete:", complete)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
