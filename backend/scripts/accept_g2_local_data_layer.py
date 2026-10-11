"""Read-only G2 functional acceptance on a reconciled AUGUR DuckDB copy.

Check real geo catalog / query results using the application's data access
layer without changing the source or the copy. Does not certify observation
boundary vintages or full application HTTP/browser operability.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import duckdb

from app.db import analytics

RETIRED = {"IE01", "IE02", "PT16", "PT17", "PT18"}
COUNTRIES = ("ESP", "IRL", "PRT")


def verify(database: Path) -> dict:
    if not database.is_file():
        raise FileNotFoundError(database)
    old_settings = analytics.settings
    analytics.settings = SimpleNamespace(duckdb_path=database)
    failures = []
    results = {}
    try:
        con = duckdb.connect(str(database), read_only=True)
        try:
            original_count = con.execute("SELECT COUNT(*) FROM subnational_observations").fetchone()[0]
            corrected = con.execute("""
                SELECT COUNT(*) FROM subnational_observations
                WHERE geography_system='NUTS_UNSPECIFIED'
                AND geo_code IN ('IE01','IE02','PT16','PT17','PT18')
            """).fetchone()[0]
            false_claims = con.execute("""
                SELECT COUNT(*) FROM subnational_observations
                WHERE geography_system='NUTS_2024'
                AND geo_code IN ('IE01','IE02','PT16','PT17','PT18')
            """).fetchone()[0]
            false_catalog = con.execute("""
                SELECT COUNT(*) FROM geography_registry
                WHERE geography_system='NUTS_2024'
                AND source_geo_code IN ('IE01','IE02','PT16','PT17','PT18')
            """).fetchone()[0]
            results["stored_observation_count"] = original_count
            results["retired_code_unverified_observations"] = corrected
            results["retired_code_false_nuts2024_observations"] = false_claims
            results["retired_code_false_current_catalog"] = false_catalog
            if (original_count, corrected, false_claims, false_catalog) != (1827, 172, 0, 0):
                failures.append("Reconciled storage counts differ from G2 accepted snapshot")
        finally:
            con.close()

        catalog = {}
        for country in COUNTRIES:
            items = analytics.geographies_for_country(country)
            current = [r for r in items if r["geography_system"] == "NUTS_2024"]
            obsolete = sorted(RETIRED & {str(r["source_geo_code"]).upper() for r in current})
            catalog[country] = {
                "current_with_evidence": len(current),
                "example_codes": [r["source_geo_code"] for r in current[:5]],
                "retired_current_codes": obsolete,
            }
            if obsolete:
                failures.append(f"{country} catalog exposes obsolete current codes: {obsolete}")
        results["catalog"] = catalog

        asturias = analytics.latest_subnational_observations("ES12", geography_system="NUTS_2024")
        results["ES12_current_indicators"] = len(asturias)
        if not asturias:
            failures.append("ES12 current-code observations not accessible via data layer")

        unknown = analytics.latest_subnational_observations("IE01", geography_system="NUTS_UNSPECIFIED")
        results["IE01_unversioned_indicators"] = len(unknown)
        if not unknown:
            failures.append("IE01 historical evidence inaccessible via data layer")
        wrong = analytics.latest_subnational_observations("IE01", geography_system="NUTS_2024")
        if wrong:
            failures.append("IE01 still queryable as NUTS_2024 observations")

        coverage = analytics.geography_coverage_status()
        results["coverage_status_countries"] = sorted({
            row["country_iso3"] for row in coverage["coverage"]
            if row.get("country_iso3")
        })
    finally:
        analytics.settings = old_settings
    return {"passed": not failures, "scope": "g2_local_data_layer_acceptance",
            "mutated_database": False, "results": results, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.db)
    print(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
