"""Read-only change impact analysis for AUGUR, based on existing audit inventory.

Usage: python backend/scripts/change_impact.py --base origin/main
       python backend/scripts/change_impact.py --changed-file frontend/src/components/ComparePanel.tsx
Run from a Git checkout. Reports conservative, static relationships, not complete coverage.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "docs/audit/inventory.json"

CRITICAL = {
    "frontend/src/components/ComparePanel.tsx": (
        "backend/app/api/", "frontend/tests/e2e/", "backend/tests/"
    ),
    "frontend/src/App.tsx": (
        "frontend/src/lib/routing.ts", "frontend/tests/e2e/", "backend/app/api/"
    ),
    "backend/app/db/write_contract.py": (
        "backend/app/db/analytics.py", "backend/tests/test_observation_write_contract.py"
    ),
    "backend/app/ingestion/imf_weo_official.py": (
        "backend/tests/test_imf_weo_official_source.py",
    ),
}


def changed_from_git(base: str) -> list[str]:
    # No remote fetch, clean, reset or file writes. Let invalid revisions fail.
    result = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--name-only", "--diff-filter=ACMRT", f"{base}...HEAD"],
        capture_output=True, text=True, check=True,
    )
    return sorted(set(result.stdout.splitlines()))


def analyze(changed: list[str], inventory: dict) -> dict:
    indexed = {entry["path"]: entry for entry in inventory.get("files", [])}
    results = []
    for path in sorted(set(changed)):
        entry = indexed.get(path, {})
        importers = entry.get("imported_by", [])
        imports = entry.get("resolved_local_imports", [])
        contracts = list(CRITICAL.get(path, ()))
        tests = sorted(set(
            dependency for dependency in importers + imports
            if "/tests/" in dependency or dependency.startswith("frontend/tests/")
        ))
        relevant_tests = sorted(set(
            tests + [hint for hint in contracts if "/tests/" in hint]
        ))
        risks = []
        if path.endswith((".ts", ".tsx", ".js", ".jsx")):
            risks.append("TypeScript/JavaScript imports and runtime relationships not indexed by Python AST")
        if path not in indexed:
            risks.append("Path absent from tracked inventory; graph may be stale or out of scope")
        if entry.get("review_status") == "stale_review":
            risks.append("Prior source review invalidated by hash change")
        if not relevant_tests and path.startswith(("backend/app/", "frontend/src/")):
            risks.append("No directly mapped regression test; inspect affected contracts manually")
        results.append({
            "path": path, "importers": importers,
            "local_imports": imports, "contract_hints": contracts,
            "test_hints": relevant_tests, "uncovered_risks": risks,
        })
    return {
        "method": "existing audited Python import graph + explicit cross-boundary hints",
        "complete_graph": False, "changed_files": len(results),
        "items": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Git merge-base ref (no fetch performed)")
    parser.add_argument("--changed-file", action="append", default=[], help="Repeat for explicit paths")
    args = parser.parse_args()
    if not args.base and not args.changed_file:
        parser.error("Provide --base or --changed-file")
    changed = changed_from_git(args.base) if args.base else []
    changed += args.changed_file
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    print(json.dumps(analyze(changed, inventory), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
