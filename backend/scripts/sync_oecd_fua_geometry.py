from __future__ import annotations

import argparse
import json

import httpx

from app.catalog import EU_MEMBER_ISO3, OECD_MEMBER_ISO3
from app.db.analytics import country_registry, geography_geometry_coverage_status
from app.db.bootstrap import initialize_datastores
from app.ingestion.oecd_fua_geometry import (
    GeometrySourceRestricted,
    sync_oecd_fua_geometries_for_countries,
)
from app.ingestion.world_bank import WorldBankAdapter


def _targets(requested: list[str] | None) -> set[str]:
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
        adapter = WorldBankAdapter(timeout_seconds=90, max_retries=3)
        try:
            if requested:
                for code in sorted(missing):
                    adapter.ensure_country_registered(code)
            else:
                adapter.register_country_catalog()
        finally:
            adapter.close()

    registry = {
        country["iso3"]: country
        for country in country_registry()
    }
    return {
        code
        for code in requested_codes
        if registry.get(code, {}).get("oecd_member")
        and not registry.get(code, {}).get("eu_member")
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize official OECD city/FUA boundary geometries."
    )
    parser.add_argument("--countries", nargs="+")
    args = parser.parse_args()

    initialize_datastores()
    targets = _targets(args.countries)

    if not targets:
        print(json.dumps({
            "source_id": "OECD",
            "geography_system": "OECD_FUA",
            "status": "no_target_countries",
            "rows": 0,
        }, indent=2))
        return 0

    try:
        result = sync_oecd_fua_geometries_for_countries(targets)
    except GeometrySourceRestricted as exc:
        print(json.dumps({
            "source_id": "OECD",
            "geography_system": "OECD_FUA",
            "status": "source_access_restricted",
            "target_countries": sorted(targets),
            "rows": 0,
            "error": str(exc),
            "notes": [
                "OECD publishes official CITY/FUA boundary archives.",
                "The current environment is not allowed to download the archive.",
                "AUGUR keeps source-native urban evidence usable without substituting third-party geometry.",
            ],
        }, indent=2))
        return 0
    except httpx.HTTPError as exc:
        print(json.dumps({
            "source_id": "OECD",
            "geography_system": "OECD_FUA",
            "status": "source_request_failed",
            "target_countries": sorted(targets),
            "rows": 0,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }, indent=2))
        return 2

    payload = {
        "source_id": "OECD",
        **result,
        "geometry_coverage": geography_geometry_coverage_status(),
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if result["rows"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
