from __future__ import annotations

import argparse
import json

from app.catalog import EU_MEMBER_ISO3, OECD_MEMBER_ISO3
from app.db.analytics import (
    country_record,
    country_registry,
    geography_coverage_status,
)
from app.db.bootstrap import initialize_datastores
from app.ingestion.oecd_fua import (
    DEFAULT_KEY,
    POPULATION_DEFAULT_KEY,
    DEPENDENCY_DEFAULT_KEY,
    LABOUR_DEFAULT_KEY,
    TRANSPORT_DEFAULT_KEY,
    OECDFUAAdapter,
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
        description=(
            "Synchronize OECD non-EU Functional Urban Area / city evidence."
        )
    )
    parser.add_argument("--countries", nargs="+")
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int)
    parser.add_argument(
        "--density-key",
        default=DEFAULT_KEY,
        help="Optional OECD FUA density SDMX key.",
    )
    parser.add_argument(
        "--population-key",
        default=POPULATION_DEFAULT_KEY,
        help="Optional OECD FUA population SDMX key.",
    )
    parser.add_argument(
        "--dependency-key",
        default=DEPENDENCY_DEFAULT_KEY,
        help="Optional OECD FUA dependency-ratio SDMX key.",
    )
    parser.add_argument(
        "--labour-key",
        default=LABOUR_DEFAULT_KEY,
        help="Optional OECD FUA labour-rate SDMX key.",
    )
    parser.add_argument(
        "--transport-key",
        default=TRANSPORT_DEFAULT_KEY,
        help="Optional OECD FUA public-transport-access SDMX key.",
    )
    args = parser.parse_args()

    initialize_datastores()
    targets = _target_countries(args.countries)

    if not targets:
        print(json.dumps({
            "source_id": "OECD",
            "geography_system": "OECD_FUA",
            "status": "no_registered_non_eu_oecd_countries",
            "rows": 0,
        }, indent=2))
        return 0

    countries = country_registry()
    adapter = OECDFUAAdapter(timeout_seconds=180, max_retries=3)
    try:
        density = adapter.sync_density(
            countries=countries,
            allowed_country_iso3=targets,
            start_year=args.start_year,
            end_year=args.end_year,
            key=args.density_key,
        )
        population = adapter.sync_population(
            countries=countries,
            allowed_country_iso3=targets,
            start_year=max(args.start_year, 2021),
            end_year=args.end_year,
            key=args.population_key,
        )
        dependency = adapter.sync_dependency(
            countries=countries,
            allowed_country_iso3=targets,
            start_year=max(args.start_year, 2021),
            end_year=args.end_year,
            key=args.dependency_key,
        )
        labour = adapter.sync_labour(
            countries=countries,
            allowed_country_iso3=targets,
            start_year=max(args.start_year, 2021),
            end_year=args.end_year,
            key=args.labour_key,
        )
        transport = adapter.sync_transport(
            countries=countries,
            allowed_country_iso3=targets,
            start_year=max(args.start_year, 2019),
            end_year=args.end_year,
            key=args.transport_key,
        )
    finally:
        adapter.close()

    total_rows = (
        density["rows"]
        + population["rows"]
        + dependency["rows"]
        + labour["rows"]
        + transport["rows"]
    )
    datasets = {
        "density": density,
        "population": population,
        "dependency": dependency,
        "labour": labour,
        "transport": transport,
    }
    complete = all(item["complete"] for item in datasets.values())
    missing_countries_by_dataset = {
        name: item["missing_countries"]
        for name, item in datasets.items()
        if item["missing_countries"]
    }

    payload = {
        "source_id": "OECD",
        "geography_system": "OECD_FUA",
        "target_country_count": len(targets),
        "target_countries": sorted(targets),
        "rows": total_rows,
        "status": "complete" if complete else "partial",
        "complete": complete,
        "missing_countries_by_dataset": missing_countries_by_dataset,
        "datasets": datasets,
        "geography_coverage": geography_coverage_status(),
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if total_rows > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
