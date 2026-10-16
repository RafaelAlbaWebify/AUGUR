"""Read-only forensic comparison of stored employment rates with Eurostat age cohorts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

from app.core.config import settings
from app.ingestion.eurostat import EurostatAdapter
from app.services.regional_evidence import REGIONAL_INDICATORS

SAMPLE_CODES = ("ES11", "ES30", "IE04", "PT11", "PT20", "PT30")
AGES = ("Y15-64", "Y20-64")
REFERENCE_PERIOD = 2025
TOLERANCE = 0.051


def inspect(db_path: Path, adapter: EurostatAdapter, codes=SAMPLE_CODES) -> dict:
    config = next(x for x in REGIONAL_INDICATORS
                  if x["indicator_id"] == "regional_employment_rate")
    con = duckdb.connect(str(db_path), read_only=True)
    records = []
    try:
        for geo in codes:
            rows = con.execute(
                """SELECT value, unit, source_id, dataset_id
                   FROM subnational_observations
                   WHERE geo_code=? AND geography_system='NUTS_2024'
                   AND indicator_id='regional_employment_rate' AND period=?""",
                [geo, REFERENCE_PERIOD],
            ).fetchall()
            if len(rows) != 1:
                records.append({"geo_code": geo, "status": "local_not_unique",
                                "local_row_count": len(rows)})
                continue

            local, unit, source, dataset = rows[0]
            record = {"geo_code": geo, "status": "diagnostic_only",
                      "local_value": float(local),
                      "local_contract_valid": (unit, source, dataset) ==
                      ("percent", "EUROSTAT", config["dataset_id"]),
                      "age_cohorts": []}
            for age in AGES:
                filters = {**config["filters"], "geo": geo,
                           "age": age, "time": str(REFERENCE_PERIOD)}
                try:
                    payload = adapter.fetch_dataset(config["dataset_id"], filters)
                    normalized = adapter.normalize(
                        geo,
                        {"indicator_id": config["indicator_id"],
                         "dataset_id": config["dataset_id"], "unit": config["unit"],
                         "dimension_values": filters},
                        payload,
                    )
                    cohort = [row for row in normalized
                              if row["period"] == REFERENCE_PERIOD
                              and row.get("source_dimensions", {}).get("age") == age]
                    if len(cohort) != 1:
                        record["age_cohorts"].append({
                            "age": age, "status": "missing_or_ambiguous",
                            "provider_row_count": len(cohort)})
                        continue
                    row = cohort[0]
                    delta = round(float(local) - row["value"], 4)
                    record["age_cohorts"].append({
                        "age": age, "status": "paired_unverified",
                        "provider_value": row["value"],
                        "signed_delta_local_minus_provider": delta,
                        "within_tolerance": abs(float(local) - row["value"]) <= TOLERANCE,
                        "provider_dimensions": row.get("source_dimensions"),
                        "provider_source_status": row.get("source_observation_status"),
                    })
                except Exception as exc:
                    record["age_cohorts"].append({"age": age, "status": "source_error",
                                                  "error_type": type(exc).__name__})
            records.append(record)
    finally:
        con.close()
    return {
        "status": "age_cohort_forensics_not_source_or_vintage_acceptance",
        "sample_codes": list(codes),
        "tolerance_percentage_points": TOLERANCE,
        "records": records,
        "warning": "Age cohort value resemblance cannot prove which filters generated an unprovenanced historic row.",
    }


def registered_pilot_codes(db_path: Path) -> tuple[str, ...]:
    """Read all locally registered 2025 pilot employment regions, without writes."""
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        return tuple(row[0] for row in conn.execute(
            """SELECT DISTINCT s.geo_code
               FROM subnational_observations s
               JOIN geography_registry g
                 ON g.source_geo_code=s.geo_code
                AND g.geography_system=s.geography_system
                AND LOWER(g.geo_level)=LOWER(s.geo_level)
               WHERE s.indicator_id='regional_employment_rate'
                 AND s.period=2025 AND s.geography_system='NUTS_2024'
                 AND g.country_iso3 IN ('ESP','IRL','PRT')
               ORDER BY s.geo_code"""
        ).fetchall())
    finally:
        conn.close()


def summarize(report: dict) -> dict:
    counts = {"total": len(report["records"]),
              "matches_15_64": 0, "matches_20_64": 0,
              "unresolved": 0}
    for record in report["records"]:
        cohorts = {entry["age"]: entry for entry in record.get("age_cohorts", [])}
        if record.get("status") != "diagnostic_only" or any(
            cohorts.get(age, {}).get("status") != "paired_unverified"
            for age in AGES
        ):
            counts["unresolved"] += 1
            continue
        if cohorts["Y15-64"]["within_tolerance"]:
            counts["matches_15_64"] += 1
        if cohorts["Y20-64"]["within_tolerance"]:
            counts["matches_20_64"] += 1
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--all-registered", action="store_true",
                        help="Audit every locally registered 2025 ESP/IRL/PRT NUTS2 employment region")
    args = parser.parse_args()
    codes = registered_pilot_codes(settings.duckdb_path) if args.all_registered else SAMPLE_CODES
    adapter = EurostatAdapter(timeout_seconds=90.0, max_retries=2)
    try:
        result = inspect(settings.duckdb_path, adapter, codes=codes)
    finally:
        adapter.close()
    result["summary"] = summarize(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "regions": len(result["records"])}))


if __name__ == "__main__":
    main()
