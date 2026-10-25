"""Explicit, guarded national source-revision application.

Default is DRY RUN. --apply requires a verified audit JSON and a distinct
backup path, preferably in Downloads. Does not accept arbitrary indicators.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import duckdb
from app.core.config import settings

ALLOWED = {
    ("ESP", "public_debt_gdp", 2025, "EUROSTAT", "gov_10dd_edpt1"),
    ("IRL", "public_debt_gdp", 2025, "EUROSTAT", "gov_10dd_edpt1"),
    ("ESP", "inflation_cpi", 2025, "WORLD_BANK", "WDI"),
}
REQUIRED = {"match", "value_drift"}


def prepare(audit: dict) -> list[dict]:
    if audit.get("scope") != "read_only_provider_reconciliation":
        raise ValueError("Unsupported audit scope")
    if audit.get("rows") != len(audit.get("results", [])):
        raise ValueError("Incomplete audit")
    proposals = []
    seen = set()
    for item in audit["results"]:
        if item.get("status") not in REQUIRED | {"vintage_unverifiable"}:
            raise ValueError(f"Unexpected audit state: {item.get('status')}")
        if item["status"] != "value_drift":
            continue
        key = (item["country"], item["indicator_id"], item["period"],
               item["provider"], item["stored_dataset"])
        if key not in ALLOWED or key in seen:
            raise ValueError(f"Unapproved or duplicate revision: {key}")
        seen.add(key)
        if not isinstance(item.get("current_value"), (int, float)) or not isinstance(item.get("stored_value"), (int, float)):
            raise ValueError("Missing numeric revision evidence")
        proposals.append(dict(key=key, before=item["stored_value"],
                              after=item["current_value"], source_updated_at=item.get("source_updated_at")))
    if seen != ALLOWED:
        raise ValueError(f"Expected all three reviewed revisions; found {len(seen)}")
    return proposals


def apply(db_path: Path, proposals: list[dict], backup_path: Path, commit: bool = False) -> dict:
    if not db_path.is_file():
        raise FileNotFoundError("Existing DuckDB missing; no new DB will be created")
    if backup_path.exists():
        raise FileExistsError("Backup output exists: choose an unused Downloads filename")
    if backup_path.resolve() == db_path.resolve():
        raise ValueError("Backup cannot overwrite the database")
    # Preflight is always read-only; verify all exact keys/values before any mutation.
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        verified = []
        for proposal in proposals:
            country, indicator, year, source, dataset = proposal["key"]
            rows = con.execute(
                """SELECT value, unit, dataset_id, observation_type, retrieved_at,
                          source_updated_at, source_observation_status, source_decimal
                   FROM observations
                   WHERE country_iso3=? AND indicator_id=? AND period=? AND source_id=?""",
                [country, indicator, year, source]).fetchall()
            if len(rows) != 1 or rows[0][2] != dataset or rows[0][3] != "observed":
                raise ValueError(f"Observation identity changed: {proposal['key']}")
            if abs(float(rows[0][0]) - float(proposal["before"])) > 1e-8:
                raise ValueError(f"Observation changed since audit: {proposal['key']}")
            verified.append({"country": country, "indicator": indicator, "period": year,
                             "source": source, "dataset": dataset, "before": rows[0][0],
                             "after": proposal["after"], "unit": rows[0][1],
                             "source_updated_at_before": rows[0][5],
                             "source_updated_at_after": proposal["source_updated_at"],
                             "retrieved_at_before": str(rows[0][4]),
                             "status_before": rows[0][6], "source_decimal_before": rows[0][7]})
    finally:
        con.close()
    report = {"status": "preflight_snapshot",
              "audit_scope": "three_reviewed_national_revisions",
              "changes": verified, "operator_database": str(db_path),
              "created_at": datetime.now(timezone.utc).isoformat()}
    # Preserve rollback evidence before opening DB in write mode.
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with backup_path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, default=str)
    if not commit:
        return report
    con = duckdb.connect(str(db_path))
    try:
        con.execute("BEGIN TRANSACTION")
        for row in verified:
            con.execute(
                """UPDATE observations SET value=?, source_updated_at=?, retrieved_at=?
                   WHERE country_iso3=? AND indicator_id=? AND period=? AND source_id=?
                     AND dataset_id=? AND observation_type='observed' AND value=?""",
                [row["after"], row["source_updated_at_after"], datetime.now(timezone.utc),
                 row["country"], row["indicator"], row["period"], row["source"],
                 row["dataset"], row["before"]]).rowcount
            # DuckDB cursor rowcount may be -1; independently verify inside tx.
            current = con.execute(
                """SELECT value FROM observations WHERE country_iso3=? AND indicator_id=?
                   AND period=? AND source_id=? AND dataset_id=?""",
                [row["country"], row["indicator"], row["period"], row["source"], row["dataset"]]).fetchall()
            if len(current) != 1 or abs(float(current[0][0])-float(row["after"])) > 1e-8:
                raise ValueError("Write verification failed; transaction rolled back")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()
    report["status"] = "applied"
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    proposals = prepare(json.loads(args.audit.read_text(encoding="utf-8")))
    result = apply(settings.duckdb_path, proposals, args.backup, commit=args.apply)
    print(json.dumps({"status": result["status"], "changes": len(result["changes"]),
                      "backup": str(args.backup)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
