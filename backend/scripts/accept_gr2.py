"""GR-2 consolidated, strictly read-only local acceptance report.

Execute from backend/: python -m scripts.accept_gr2 --output PATH.json
This is diagnostic evidence, not permission to publish rankings or change DB data.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import duckdb

from app.core.config import settings
from app.ingestion.eurostat import EurostatAdapter
from app.services.ranking_eligibility import PILOT_CONTRACTS
from scripts.reconcile_ranking_eurostat import reconcile
from scripts.inspect_ranking_employment_age import inspect as inspect_ages, registered_pilot_codes, summarize


def database_evidence(db_path: Path) -> dict:
    """Read-only local invariants and physical fingerprint, never checkpoint."""
    if not db_path.is_file():
        raise FileNotFoundError(db_path)
    digest = hashlib.sha256()
    with db_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        integrity = [str(row[0]) for row in con.execute("PRAGMA database_size").fetchall()]
        names = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        missing = sorted({"subnational_observations", "geography_registry"} - names)
        if missing:
            return {"sha256": digest.hexdigest(), "size_bytes": db_path.stat().st_size,
                    "status": "missing_tables", "missing_tables": missing,
                    "database_size": integrity}
        cols = {row[1] for row in con.execute("PRAGMA table_info('subnational_observations')").fetchall()}
        rows = {}
        for indicator, contract in PILOT_CONTRACTS.items():
            c = con.execute(
                """SELECT count(*), count(DISTINCT geo_code),
                          sum(CASE WHEN value IS NULL THEN 1 ELSE 0 END)
                   FROM subnational_observations
                   WHERE indicator_id=? AND period=? AND geography_system=?""",
                [indicator, contract.period, contract.geography_system],
            ).fetchone()
            provenance = {}
            for field in ("request_filters_json", "response_dimensions_json",
                          "source_observation_status"):
                if field in cols:
                    provenance[field] = con.execute(
                        f"""SELECT count(*) FILTER (WHERE {field} IS NOT NULL)
                            FROM subnational_observations
                            WHERE indicator_id=? AND period=? AND geography_system=?""",
                        [indicator, contract.period, contract.geography_system],
                    ).fetchone()[0]
                else:
                    provenance[field] = None
            rows[indicator] = {"records": c[0], "distinct_geo_codes": c[1],
                               "null_values": c[2] or 0, "metadata_present": provenance}
        return {"status": "read_only_inventory", "sha256": digest.hexdigest(),
                "size_bytes": db_path.stat().st_size, "database_size": integrity,
                "pilot_rows": rows}
    finally:
        con.close()


def accept(db_path: Path, adapter: EurostatAdapter, *, full_age_audit=True) -> dict:
    before = database_evidence(db_path)
    if before["status"] != "read_only_inventory":
        return {"status": "blocked_schema", "database": before}
    problems = {}
    reports = {}
    try:
        reports["source_reconciliation"] = reconcile(db_path, adapter)
    except Exception as exc:
        problems["source_reconciliation"] = type(exc).__name__
    if full_age_audit:
        try:
            codes = registered_pilot_codes(db_path)
            ages = inspect_ages(db_path, adapter, codes=codes)
            ages["summary"] = summarize(ages)
            reports["employment_age_cohorts"] = ages
        except Exception as exc:
            problems["employment_age_cohorts"] = type(exc).__name__
    after = database_evidence(db_path)
    unchanged = (before["sha256"] == after["sha256"]
                 and before["size_bytes"] == after["size_bytes"])
    problems.update({} if unchanged else {"database_modified": "hash_or_size_changed"})
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "diagnostic_complete_not_certified" if not problems else "diagnostic_incomplete",
        "database": before,
        "database_unchanged": unchanged,
        "reports": reports,
        "errors": problems,
        "acceptance_gates": {
            "production_data_mutation_authorized": False,
            "source_quality_status_policy": "pending_official_review",
            "observation_boundary_vintage": "unverified",
            "numerical_rankings": "blocked",
            "operator_ui_acceptance": "not_performed",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--skip-age-audit", action="store_true")
    args = parser.parse_args()
    adapter = EurostatAdapter(timeout_seconds=90.0, max_retries=2)
    try:
        result = accept(settings.duckdb_path, adapter, full_age_audit=not args.skip_age_audit)
    finally:
        adapter.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "database_unchanged": result.get("database_unchanged"),
                      "output": str(args.output)}))


if __name__ == "__main__":
    main()
