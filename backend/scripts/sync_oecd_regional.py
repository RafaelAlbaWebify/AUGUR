from __future__ import annotations

import argparse
import json

from app.catalog import EU_MEMBER_ISO3, OECD_MEMBER_ISO3
from app.db.analytics import (
    country_record,
    country_registry,
    geography_coverage_status,
    stale_geography_countries,
)
from app.db.bootstrap import initialize_datastores
from app.ingestion.oecd_regional import (
    DENSITY_DEFAULT_KEY,
    POPULATION_DEFAULT_KEY,
    DEMOGRAPHY_DEFAULT_KEY,
    LABOUR_DEFAULT_KEY,
    GDP_DEFAULT_KEY,
    INCOME_DEFAULT_KEY,
    SAFETY_DEFAULT_KEY,
    OECDRegionalAdapter,
)
from app.ingestion.world_bank import WorldBankAdapter


def _target_countries(requested: list[str] | None) -> set[str]:
    requested_codes = (
        {value.upper() for value in requested}
        if requested
        else set(OECD_MEMBER_ISO3) - set(EU_MEMBER_ISO3)
    )

    existing = {
        country["iso3"]
        for country in country_registry()
    }
    missing = requested_codes - existing

    if missing:
        world_bank = WorldBankAdapter(timeout_seconds=90, max_retries=3)
        try:
            if requested:
                for code in sorted(missing):
                    world_bank.ensure_country_registered(code)
            else:
                # One authoritative catalog request is cheaper and more robust
                # than one metadata request per OECD country. It also prepares
                # the local registry for future global analysis.
                world_bank.register_country_catalog()
        finally:
            world_bank.close()

    registry = {
        country["iso3"]: country
        for country in country_registry()
    }
    return {
        code
        for code in requested_codes
        if (
            registry.get(code, {}).get("oecd_member")
            and not registry.get(code, {}).get("eu_member")
        )
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize OECD non-EU TL2/TL3 regional evidence."
    )
    parser.add_argument("--countries", nargs="+")
    parser.add_argument("--start-year", type=int, default=2021)
    parser.add_argument("--end-year", type=int)
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=24.0,
        help="Skip countries with provider-native evidence newer than this many hours.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore local freshness and force a provider refresh.",
    )
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
    parser.add_argument(
        "--demography-key",
        default=DEMOGRAPHY_DEFAULT_KEY,
        help="Optional OECD demographic SDMX key.",
    )
    parser.add_argument(
        "--labour-key",
        default=LABOUR_DEFAULT_KEY,
        help="Optional OECD regional labour-rate SDMX key.",
    )
    parser.add_argument(
        "--gdp-key",
        default=GDP_DEFAULT_KEY,
        help="Optional OECD regional GDP-per-capita PPP SDMX key.",
    )
    parser.add_argument(
        "--income-key",
        default=INCOME_DEFAULT_KEY,
        help="Optional OECD regional disposable-income PPP SDMX key.",
    )
    parser.add_argument(
        "--safety-key",
        default=SAFETY_DEFAULT_KEY,
        help="Optional OECD regional safety SDMX key.",
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

    requested_targets = set(targets)
    if not args.force:
        targets = stale_geography_countries(
            "OECD_TL_2024",
            targets,
            [],
            max_age_hours=args.max_age_hours,
        )

    skipped_fresh = sorted(requested_targets - set(targets))
    if not targets:
        print(json.dumps({
            "source_id": "OECD",
            "geography_system": "OECD_TL_2024",
            "status": "fresh_local_evidence",
            "target_country_count": len(requested_targets),
            "skipped_fresh_countries": skipped_fresh,
            "max_age_hours": args.max_age_hours,
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
        demography = adapter.sync_demography(
            allowed_country_iso3=targets,
            start_year=args.start_year,
            end_year=args.end_year,
            key=args.demography_key,
        )
        labour = adapter.sync_labour(
            allowed_country_iso3=targets,
            start_year=args.start_year,
            end_year=args.end_year,
            key=args.labour_key,
        )
        gdp = adapter.sync_gdp(
            allowed_country_iso3=targets,
            start_year=args.start_year,
            end_year=args.end_year,
            key=args.gdp_key,
        )
        income = adapter.sync_income(
            allowed_country_iso3=targets,
            start_year=args.start_year,
            end_year=args.end_year,
            key=args.income_key,
        )
        safety = adapter.sync_safety(
            allowed_country_iso3=targets,
            start_year=args.start_year,
            end_year=args.end_year,
            key=args.safety_key,
        )
    finally:
        adapter.close()

    total_rows = (
        density["rows"]
        + population["rows"]
        + demography["rows"]
        + labour["rows"]
        + gdp["rows"]
        + income["rows"]
        + safety["rows"]
    )
    payload = {
        "source_id": "OECD",
        "target_country_count": len(requested_targets),
        "refreshed_country_count": len(targets),
        "target_countries": sorted(requested_targets),
        "refreshed_countries": sorted(targets),
        "skipped_fresh_countries": skipped_fresh,
        "max_age_hours": args.max_age_hours,
        "rows": total_rows,
        "datasets": {
            "density": density,
            "population": population,
            "demography": demography,
            "labour": labour,
            "gdp": gdp,
            "income": income,
            "safety": safety,
        },
        "geography_coverage": geography_coverage_status(),
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if total_rows > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
