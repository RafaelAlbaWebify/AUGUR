"""Compare stored geography identities with official NUTS 2024 catalog.

The report compares code membership only, never statistical completeness.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

COUNTRIES = {"ESP": "ES", "IRL": "IE", "PRT": "PT"}


def compare_catalogs(official: dict, local: dict) -> dict:
    if official.get("scope") != "official_gisco_nuts_2024_catalog_only":
        raise ValueError("Official catalog has unexpected scope")
    if local.get("status") != "observed_local_registry_only":
        raise ValueError("Local provenance has unexpected scope")
    results = []
    for iso3, iso2 in COUNTRIES.items():
        for level in ("nuts2", "nuts3"):
            official_codes = set(official["catalogs"][level][iso2]["codes"])
            stored = {
                entry["source_geo_code"]: entry
                for entry in local["items"]
                if entry["country_iso3"] == iso3
                and entry["geo_level"].lower() == level
                and entry["geography_system"] == "NUTS_2024"
            }
            local_codes = set(stored)
            results.append({
                "country_iso3": iso3,
                "geo_level": level,
                "official_catalog_count": len(official_codes),
                "local_registry_count": len(local_codes),
                "matching_codes": sorted(local_codes & official_codes),
                "official_codes_not_registered": sorted(official_codes - local_codes),
                "registered_codes_not_in_official_catalog": sorted(local_codes - official_codes),
                "matching_codes_without_observations": sorted(
                    code for code in local_codes & official_codes
                    if not stored[code]["has_evidence"]
                ),
            })
    return {
        "scope": "exact_geo_code_membership_audit",
        "warning": (
            "A mismatch may reflect temporal boundary changes, catalog differences "
            "or incomplete local discovery. This is not indicator availability or "
            "statistical comparability, and does not automatically delete records."
        ),
        "results": results,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--official", type=Path, required=True)
    p.add_argument("--local", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    official = json.loads(a.official.read_text(encoding="utf-8"))
    local = json.loads(a.local.read_text(encoding="utf-8"))
    result = compare_catalogs(official, local)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in result["results"]:
        print(f'{item["country_iso3"]} {item["geo_level"]}: '
              f'{len(item["matching_codes"])} matching, '
              f'{len(item["official_codes_not_registered"])} not registered, '
              f'{len(item["registered_codes_not_in_official_catalog"])} nonmatching')


if __name__ == "__main__":
    main()
