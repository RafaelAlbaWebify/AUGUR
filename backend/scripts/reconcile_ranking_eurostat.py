"""Compare local 2025 NUTS2 pilot values to fresh Eurostat responses, read-only.

Run from backend/: python -m scripts.reconcile_ranking_eurostat --output PATH.json
No database writes, no historical provenance claims. Requires network access.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import duckdb
from app.core.config import settings
from app.ingestion.eurostat import EurostatAdapter
from app.services.regional_evidence import REGIONAL_INDICATORS
from app.services.ranking_eligibility import PILOT_CONTRACTS


def reconcile(db_path: Path, adapter: EurostatAdapter, tolerance: float = 0.051) -> dict:
    conn = duckdb.connect(str(db_path), read_only=True)
    results = {}
    try:
        for indicator_id, contract in PILOT_CONTRACTS.items():
            config = next(c for c in REGIONAL_INDICATORS if c["indicator_id"] == indicator_id)
            stored = conn.execute(
                """SELECT g.country_iso3, s.geo_code, s.value, s.unit, s.source_id, s.dataset_id
                   FROM subnational_observations s
                   JOIN geography_registry g ON g.source_geo_code=s.geo_code
                     AND g.geography_system=s.geography_system
                     AND LOWER(g.geo_level)=LOWER(s.geo_level)
                   WHERE s.indicator_id=? AND s.period=? AND s.geography_system=?
                   ORDER BY g.country_iso3, s.geo_code""",
                [indicator_id, contract.period, contract.geography_system],
            ).fetchall()
            by_geo = {}
            duplicate_codes = set()
            for country, code, value, unit, source, dataset in stored:
                if code in by_geo:
                    duplicate_codes.add(code)
                by_geo[code] = (country, float(value), unit, source, dataset)
            codes = sorted(by_geo)
            actual = {}
            errors = {}
            # One request per metric and country; no per-geo network hammering.
            for country in sorted({v[0] for v in by_geo.values()}):
                group = sorted(k for k,v in by_geo.items() if v[0] == country)
                try:
                    response = adapter.fetch_dataset(
                        contract.dataset_id,
                        {**config["filters"], "geo": group, "time": str(contract.period)},
                    )
                    for row in adapter.normalize(country, {
                        "indicator_id": indicator_id,
                        "dataset_id": contract.dataset_id, "unit": contract.unit,
                    }, response):
                        dimensions = row.get("source_dimensions") or {}
                        geo = dimensions.get("geo")
                        if geo and row["period"] == contract.period:
                            if geo in actual:
                                errors[geo] = "multiple_provider_rows"
                            else:
                                actual[geo] = row
                except Exception as exc:
                    for geo in group:
                        errors[geo] = type(exc).__name__
            issues = []
            matched = 0
            for geo in codes:
                country, value, unit, source, dataset = by_geo[geo]
                reason = None
                fresh = actual.get(geo)
                if geo in duplicate_codes:
                    reason = "duplicate_local_rows"
                elif geo in errors:
                    reason = errors[geo]
                elif (unit, source, dataset) != (contract.unit, contract.source_id, contract.dataset_id):
                    reason = "local_source_contract_mismatch"
                elif fresh is None:
                    reason = "missing_provider_observation"
                elif abs(value - fresh["value"]) > tolerance:
                    reason = "value_discrepancy"
                elif fresh.get("source_observation_status") not in (None, ""):
                    reason = "provider_quality_flag_review_required"
                if reason:
                    issues.append({"geo_code": geo, "country_iso3": country, "reason": reason})
                else:
                    matched += 1
            results[indicator_id] = {
                "period": contract.period, "dataset_id": contract.dataset_id,
                "local_records": len(stored), "unique_geographies": len(codes),
                "provider_returned_geographies": len(actual),
                "value_matches_within_tolerance": matched,
                "issue_count": len(issues), "issues": issues,
            }
    finally:
        conn.close()
    return {
        "status": "source_replay_not_boundary_vintage_certification",
        "tolerance_percentage_points": tolerance,
        "metrics": results,
        "note": "No values are exported. Provider matching alone does not certify boundary vintage or an unflagged observation's full statistical comparability.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tolerance", type=float, default=0.051)
    args = parser.parse_args()
    if not 0 <= args.tolerance <= 1:
        parser.error("Tolerance must be between 0 and 1 percentage point")
    with_adapter = EurostatAdapter(timeout_seconds=90.0, max_retries=2)
    try:
        report = reconcile(settings.duckdb_path, with_adapter, args.tolerance)
    finally:
        with_adapter.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: {"matched": v["value_matches_within_tolerance"], "issues": v["issue_count"]}
                      for k,v in report["metrics"].items()}))


if __name__ == "__main__":
    main()
