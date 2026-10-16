"""Read-only representative paired value evidence; never modifies observations."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import duckdb
from app.core.config import settings
from app.ingestion.eurostat import EurostatAdapter
from app.services.ranking_eligibility import PILOT_CONTRACTS
from app.services.regional_evidence import REGIONAL_INDICATORS
from app.services.ranking_provider_metadata import check_provider_metadata

CODES = ("ES11", "ES30", "IE04", "PT11", "PT20", "PT30")


def inspect(db_path: Path, adapter: EurostatAdapter, codes=CODES) -> dict:
    conn = duckdb.connect(str(db_path), read_only=True)
    results = []
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info('subnational_observations')").fetchall()}
        metadata_fields = ("request_filters_json", "response_dimensions_json", "source_observation_status")
        projection = ", ".join(name if name in columns else "NULL" for name in metadata_fields)
        for identifier, contract in PILOT_CONTRACTS.items():
            config = next(item for item in REGIONAL_INDICATORS if item["indicator_id"] == identifier)
            for code in codes:
                rows = conn.execute(
                    f"""SELECT value, source_id, dataset_id, {projection}
                    FROM subnational_observations
                    WHERE geo_code=? AND indicator_id=? AND period=?
                      AND geography_system=?""",
                    [code, identifier, contract.period, contract.geography_system],
                ).fetchall()
                if len(rows) != 1:
                    results.append({"indicator_id": identifier, "geo_code": code,
                                    "status": "missing_or_ambiguous_local", "local_row_count": len(rows)})
                    continue
                local, source_id, dataset, request, response, source_status = rows[0]
                filters = {**config["filters"], "geo": code, "time": str(contract.period)}
                try:
                    payload = adapter.fetch_dataset(contract.dataset_id, filters)
                    normalized = adapter.normalize(
                        code, {"indicator_id": identifier, "dataset_id": contract.dataset_id,
                               "unit": contract.unit, "dimension_values": filters}, payload)
                    matching = [item for item in normalized if item["period"] == contract.period
                                and not tuple(reason for reason in check_provider_metadata(
                                    json.dumps(item.get("source_dimensions")),
                                    item.get("source_observation_status"),
                                    geo_code=code, period=contract.period, indicator_id=identifier)
                                    if reason != "provider_status_review_required")]
                    if len(matching) != 1:
                        results.append({"indicator_id": identifier, "geo_code": code,
                                        "status": "provider_missing_or_ambiguous",
                                        "provider_matching_count": len(matching)})
                        continue
                    fresh = matching[0]
                    results.append({
                        "indicator_id": identifier, "geo_code": code,
                        "status": "paired_unverified",
                        "local_value": float(local), "provider_value": fresh["value"],
                        "signed_delta_local_minus_provider": round(float(local)-fresh["value"], 4),
                        "local_source_id": source_id, "local_dataset_id": dataset,
                        "local_request_filters": json.loads(request) if request else None,
                        "local_response_dimensions": json.loads(response) if response else None,
                        "local_source_status": source_status,
                        "provider_dimensions": fresh.get("source_dimensions"),
                        "provider_source_status": fresh.get("source_observation_status"),
                    })
                except Exception as exc:
                    results.append({"indicator_id": identifier, "geo_code": code,
                                    "status": "provider_error", "error_type": type(exc).__name__})
    finally:
        conn.close()
    return {"status": "diagnostic_not_data_acceptance", "sample_codes": list(codes),
            "privacy_note": "Contains actual statistical values for a restricted sample; review before sharing.",
            "records": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    client = EurostatAdapter(timeout_seconds=90, max_retries=2)
    try:
        report = inspect(settings.duckdb_path, client)
    finally:
        client.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "rows": len(report["records"])}))


if __name__ == "__main__":
    main()
