"""Read-only parallel source audit for Spain/Ireland; never ingests or overwrites observations.

Run: python -m scripts.audit_compare_sources --input ../compare_esp_irl_evidence.json --output ../compare_source_audit.json
Only Eurostat is live-checked in v1. All other sources are explicitly pending.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path

from app.ingestion.eurostat import EUROSTAT_SERIES, EurostatAdapter

ISO2 = {"ESP": "ES", "IRL": "IE"}
EUROSTAT_CONFIGS = {config["indicator_id"]: config for config in EUROSTAT_SERIES}


def audit_eurostat(row: dict, adapter_factory=EurostatAdapter) -> dict:
    """Fetch exactly one country/year and compare the configured source definition."""
    result = {"country": row["country_iso3"], "indicator_id": row["indicator_id"],
              "provider": row["source_id"], "period": row["period"],
              "stored_value": row["value"], "stored_dataset": row.get("dataset_id")}
    config = EUROSTAT_CONFIGS.get(row["indicator_id"])
    if config is None:
        return {**result, "status": "unsupported_config", "reason": "No national Eurostat adapter declaration"}
    if config["dataset_id"].lower() != str(row.get("dataset_id", "")).lower():
        return {**result, "status": "source_drift", "reason": "Persisted dataset differs from current ingestion contract",
                "configured_dataset": config["dataset_id"]}
    if config["unit"] != row["unit"]:
        return {**result, "status": "unit_drift", "reason": "Persisted unit differs from current ingestion contract"}
    filters = {name: (ISO2[row["country_iso3"]] if val == "__GEO__" else val)
               for name, val in config["filters"].items()}
    filters["sinceTimePeriod"] = str(row["period"])
    filters["untilTimePeriod"] = str(row["period"])
    adapter = adapter_factory()
    try:
        payload = adapter.fetch_dataset(config["dataset_id"], filters)
        observations = adapter.normalize(row["country_iso3"], config, payload)
    except Exception as exc:
        return {**result, "status": "source_error", "reason": f"{type(exc).__name__}: {exc}"[:350]}
    finally:
        adapter.close()
    target = [item for item in observations if item["period"] == row["period"]]
    if len(target) != 1:
        return {**result, "status": "missing_or_ambiguous", "count": len(target)}
    fresh = target[0]
    delta = abs(float(fresh["value"]) - float(row["value"]))
    # Compare at persisted precision rather than a guessed provider release decimal.
    tolerance = 0.5 * 10 ** (-row["source_decimal"]) if isinstance(row.get("source_decimal"), int) else 1e-8
    return {**result, "status": "match" if delta <= tolerance else "value_drift",
            "current_value": fresh["value"], "difference": delta,
            "tolerance": tolerance, "source_updated_at": fresh.get("source_updated_at"),
            "source_dimensions": fresh.get("source_dimensions")}


def audit(rows: list[dict], check_eurostat=audit_eurostat, workers: int = 4) -> dict:
    if workers < 1 or workers > 8:
        raise ValueError("workers must be between 1 and 8")
    seen = set()
    for row in rows:
        key = (row["country_iso3"], row["indicator_id"])
        if key in seen:
            raise ValueError(f"Duplicate selected indicator: {key}")
        seen.add(key)
    output = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for row in rows:
            if row["country_iso3"] not in ISO2:
                raise ValueError(f"Unsupported country: {row['country_iso3']}")
            if row["source_id"] != "EUROSTAT":
                output.append({"country": row["country_iso3"], "indicator_id": row["indicator_id"],
                               "provider": row["source_id"], "status": "provider_not_implemented",
                               "reason": "Requires an exact source-specific historical read contract"})
            else:
                futures[pool.submit(check_eurostat, row)] = row
        for future in as_completed(futures):
            output.append(future.result())
    output.sort(key=lambda item: (item["indicator_id"], item["country"]))
    counts = {}
    for row in output:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {"scope": "read_only_provider_reconciliation", "rows": len(output),
            "status_counts": counts, "results": output,
            "notes": ["No database writes or synchronization",
                      "A match certifies one source endpoint value on run date, not wider methodology or source vintage",
                      "Non-Eurostat providers explicitly pending; no silent assumption of validity"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output must differ")
    data = json.loads(args.input.read_text(encoding="utf-8"))
    if data.get("scope") != "national_latest_observed_exact_compare_selection":
        parser.error("Expected the national compare evidence export")
    report = audit(data["rows"], workers=args.workers)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"rows": report["rows"], "status_counts": report["status_counts"],
                      "output": str(args.output)}))


if __name__ == "__main__":
    main()
