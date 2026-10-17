"""CI inventory of every central DuckDB upsert writer and its protection contract.

This AST-based guard intentionally covers the shared analytics module only.
Adapter semantics, direct SQL outside analytics.py, geographic vintage and
quality-flag policy require separate source-specific verification.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

GENERIC = {"upsert_observations", "upsert_subnational_observations"}
SPECIALIZED = {
    "upsert_labour_earnings", "upsert_labour_net_earnings_reference",
    "upsert_labour_job_vacancy_rates", "upsert_labour_oja_imbalance_eu27",
    "upsert_labour_shortage_index", "upsert_labour_occupation_outlook",
    "upsert_labour_job_transitions", "upsert_environmental_health_burden",
}
SECTOR = {"upsert_regional_sector_employment"}
# These are NOT marked atomic or fully audited observation ingestion paths.
NON_OBSERVATION = {
    "upsert_country", "upsert_geographies", "upsert_geography_geometries",
}
KNOWN = GENERIC | SPECIALIZED | SECTOR | NON_OBSERVATION


def audit_source(source: str) -> dict:
    tree = ast.parse(source)
    methods = {node.name: node for node in tree.body
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
               and node.name.startswith("upsert_")}
    issues=[]
    missing = sorted(KNOWN - methods.keys())
    unexpected = sorted(methods.keys() - KNOWN)
    if missing: issues.append(f"Deleted expected write entrypoints: {missing}")
    if unexpected: issues.append(f"Unreviewed new write entrypoints: {unexpected}")

    groups={}
    for name,fn in sorted(methods.items()):
        group=("generic" if name in GENERIC else "specialized" if name in SPECIALIZED
               else "sector" if name in SECTOR else "non_observation")
        groups[name]=group
        if group=="non_observation":
            continue
        calls=set()
        strings=set()
        for child in ast.walk(fn):
            if isinstance(child, ast.Call):
                f=child.func
                calls.add(f.id if isinstance(f,ast.Name) else
                          f.attr if isinstance(f,ast.Attribute) else "")
            elif isinstance(child,ast.Constant) and isinstance(child.value,str):
                strings.add(child.value.upper())
        validator=("validate_write_batch" if group=="generic" else
                   "validate_specialized_batch" if group=="specialized" else "isfinite")
        if validator not in calls:
            issues.append(f"{name}: missing batch validation {validator}")
        if group=="sector" and "add" not in calls:
            issues.append(f"{name}: duplicate-key detection missing")
        for action in ("BEGIN TRANSACTION","COMMIT","ROLLBACK"):
            if action not in strings:
                issues.append(f"{name}: missing explicit {action}")
    return {
        "status":"passed" if not issues else "failed",
        "scope":"central_analytics_upsert_functions_only",
        "writer_count":len(methods),
        "protected_observation_writers":sum(x!="non_observation" for x in groups.values()),
        "non_observation_exceptions":sorted(NON_OBSERVATION),
        "groups":groups, "issues":issues,
        "provider_quality_or_vintage_certified":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,
        default=Path(__file__).resolve().parents[1]/"app/db/analytics.py")
    args=parser.parse_args()
    report=audit_source(args.source.read_text(encoding="utf-8"))
    print(json.dumps(report,indent=2))
    return 0 if report["status"]=="passed" else 2


if __name__=="__main__":
    raise SystemExit(main())
