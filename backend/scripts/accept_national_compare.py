"""One-shot Spain/Ireland operational acceptance without database writes.

Reads live operator DuckDB in read-only mode, checks real /api/compare,
rechecks all 58 source observations, records remaining IMF vintage gates.
Output JSON is an explicit path (recommended: Downloads).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes import router
from app.core.config import settings
from scripts.audit_compare_sources import audit
from scripts.export_compare_evidence import collect


def accept(evidence: dict, audited: dict, api_response: dict) -> dict:
    rows = evidence["rows"]
    items = api_response.get("indicators", [])
    expected = {(r["country_iso3"], r["indicator_id"]): r for r in rows}
    actual = {(country, item["indicator_id"]): value
              for item in items for country, value in item.get("countries", {}).items()}
    mismatches = []
    if api_response.get("indicator_count") != len(items):
        mismatches.append("API indicator_count differs from payload")
    if [c["iso3"] for c in api_response.get("countries", [])] != ["ESP", "IRL"]:
        mismatches.append("API country ordering/identity differs from requested pair")
    for key, row in expected.items():
        value = actual.get(key)
        if value is None:
            mismatches.append(f"API missing {key}")
            continue
        if (value.get("period") != row["period"] or
                value.get("source_id") != row["source_id"] or
                abs(float(value["value"]) - float(row["value"])) > 1e-8 * max(1, abs(row["value"]))):
            mismatches.append(f"API changed selected value or provenance {key}")
    statuses = audited.get("status_counts", {})
    if audited.get("rows") != len(rows):
        mismatches.append("Source-audit coverage incomplete")
    if sum(statuses.values()) != len(rows):
        mismatches.append("Source-audit counts incomplete")
    if len(rows) != 58 or evidence.get("country_counts") != {"ESP": 29, "IRL": 29}:
        mismatches.append("ESP/IRL national coverage differs from acceptance baseline")
    # Unverified IMF rows must remain visible, never silently accepted as match.
    imf = [r for r in audited["results"] if r["provider"] == "IMF"]
    if len(imf) != 6 or any(x["status"] != "vintage_unverifiable" for x in imf):
        mismatches.append("IMF release-vintage gate changed or disappeared")
    drift = [r for r in audited["results"] if r["status"] != "match"
             and r["status"] != "vintage_unverifiable"]
    status = "blocked" if mismatches or drift or imf else "accepted"
    return {"status": status, "api_alignment": "pass" if not any(s.startswith("API") for s in mismatches) else "fail",
            "countries": ["ESP", "IRL"], "indicators_per_country": evidence["country_counts"],
            "source_counts": statuses, "verified_observations": statuses.get("match", 0),
            "open_source_discrepancies": drift, "imf_vintage_gates": imf,
            "acceptance_findings": mismatches,
            "limitations": ["API integration is exercised via in-process real FastAPI route; frontend visual acceptance is separately covered by CI",
                            "IMF April 2026 vintage cannot be certified from mutable live DataMapper",
                            "No database modifications or synchronization were performed"]}


def run() -> dict:
    if not settings.duckdb_path.is_file():
        raise FileNotFoundError("Existing AUGUR DuckDB not found")
    evidence = collect(settings.duckdb_path)
    app = FastAPI()
    app.include_router(router, prefix="/api")
    response = TestClient(app).get("/api/compare?countries=ESP,IRL")
    response.raise_for_status()
    audited = audit(evidence["rows"])
    return accept(evidence, audited, response.json())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.suffix.lower() != ".json":
        parser.error("Output needs .json suffix")
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "api_alignment": result["api_alignment"],
                      "source_counts": result["source_counts"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
