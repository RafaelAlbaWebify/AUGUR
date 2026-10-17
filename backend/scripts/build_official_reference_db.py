"""Build a narrowly scoped, reproducible official-source DuckDB for CI.

Separate from AUGUR production schema. No user profiles or local DB files.
Does not certify NUTS boundary vintage or quality-flag comparability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import duckdb

from app.ingestion.eurostat import EurostatAdapter
from app.services.regional_evidence import REGIONAL_INDICATORS
from app.services.ranking_provider_metadata import check_provider_metadata

# Frozen PILOT inventory, not a worldwide or NUTS-complete assertion.
CODES = {
    "ESP": ("ES11","ES12","ES13","ES21","ES22","ES23","ES24","ES30","ES41","ES42","ES43","ES51","ES52","ES53","ES61","ES62","ES63","ES64","ES70"),
    "IRL": ("IE04","IE05","IE06"),
    "PRT": ("PT11","PT15","PT19","PT1A","PT1B","PT1C","PT1D","PT20","PT30"),
}
INDICATORS = ("regional_employment_rate", "regional_unemployment_rate")
PERIOD = 2025


def collect(adapter):
    configurations = {row["indicator_id"]: row for row in REGIONAL_INDICATORS}
    accepted = []
    for indicator in INDICATORS:
        config = configurations[indicator]
        for country, codes in CODES.items():
            filters = {**config["filters"], "geo": list(codes), "time": str(PERIOD)}
            payload = adapter.fetch_dataset(config["dataset_id"], filters)
            expected = set(codes)
            observed = {}
            for row in adapter.normalize(country, {
                "indicator_id": indicator, "dataset_id": config["dataset_id"],
                "unit": config["unit"],
                "dimension_values": {key: value for key, value in filters.items() if key != "geo"},
            }, payload):
                dims = row["source_dimensions"]
                code = dims.get("geo")
                if code not in expected or row["period"] != PERIOD:
                    raise ValueError(f"Unexpected provider geography/period: {indicator} {code}")
                problems = check_provider_metadata(
                    json.dumps(dims), row.get("source_observation_status"),
                    geo_code=code, period=PERIOD, indicator_id=indicator,
                )
                if set(problems) - {"provider_status_review_required"}:
                    raise ValueError(f"Provider dimension contract failed: {indicator} {code}: {problems}")
                if code in observed:
                    raise ValueError(f"Duplicate provider observation: {indicator} {code}")
                observed[code] = row
            if set(observed) != expected:
                raise ValueError(f"Incomplete provider response for {indicator} {country}: missing={sorted(expected-set(observed))}")
            accepted.extend(observed[code] for code in codes)
    return accepted


def write_reference(rows, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("Reference destination already exists")
    con = duckdb.connect(str(destination))
    try:
        con.execute("""CREATE TABLE reference_observations(
          country_iso3 VARCHAR, geo_code VARCHAR, indicator_id VARCHAR, period INTEGER,
          value DOUBLE, unit VARCHAR, source_id VARCHAR, dataset_id VARCHAR,
          source_dimensions_json VARCHAR, source_status VARCHAR, source_updated_at VARCHAR,
          retrieved_at VARCHAR,
          PRIMARY KEY (geo_code,indicator_id,period))""")
        con.execute("BEGIN TRANSACTION")
        try:
            for row in rows:
                con.execute("INSERT INTO reference_observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
                    row["country_iso3"], row["source_dimensions"]["geo"], row["indicator_id"],
                    row["period"], row["value"], row["unit"], row["source_id"], row["dataset_id"],
                    json.dumps(row["source_dimensions"], sort_keys=True),
                    row.get("source_observation_status"), row.get("source_updated_at"),
                    str(row["retrieved_at"]),
                ])
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        actual = con.execute("SELECT count(*) FROM reference_observations").fetchone()[0]
        if actual != len(INDICATORS) * sum(map(len, CODES.values())):
            raise ValueError("Reference observation cardinality mismatch")
    finally:
        con.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if Path(args.db).resolve() == Path(args.report).resolve():
        parser.error("DB and report must have separate paths")
    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        rows = collect(adapter)
    finally:
        adapter.close()
    write_reference(rows, args.db)
    report = {
        "status": "official_source_reference_only_not_vintage_certified",
        "period": PERIOD,
        "indicators": list(INDICATORS),
        "countries": {country: len(codes) for country, codes in CODES.items()},
        "observation_count": len(rows),
        "flagged_observations": [
            {"country": r["country_iso3"], "geo": r["source_dimensions"]["geo"],
             "indicator": r["indicator_id"], "status": r["source_observation_status"]}
            for r in rows if r.get("source_observation_status")
        ],
        "boundary_vintage_certified": False,
        "ranking_eligible_certified": False,
        "production_writes": 0,
        "sha256": hashlib.sha256(Path(args.db).read_bytes()).hexdigest(),
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status","observation_count","production_writes")}))


if __name__ == "__main__":
    main()
