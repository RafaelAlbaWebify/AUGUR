"""Read-only change impact analysis for AUGUR, based on existing audit inventory.

Usage: python backend/scripts/change_impact.py --base origin/main
       python backend/scripts/change_impact.py --changed-file frontend/src/components/ComparePanel.tsx
Run from a Git checkout. Reports conservative, static relationships, not complete coverage.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "docs/audit/inventory.json"

TS_IMPORT = re.compile(r"""(?:from\s+|import\s*\(\s*|require\s*\(\s*)['"]([.][^'"]+)['"]""")
TS_SUFFIXES = (".ts", ".tsx", ".js", ".jsx")
TS_IGNORED = {"node_modules", "dist", "build", "test-results"}


def typescript_edges(root: Path) -> dict[str, list[str]]:
    """Resolve literal relative TS/JS imports; dynamic patterns remain out of scope."""
    source = root / "frontend" / "src"
    if not source.exists():
        return {}
    candidates = {path.resolve(): path.relative_to(root).as_posix()
                  for path in source.rglob("*")
                  if path.is_file() and path.suffix in TS_SUFFIXES
                  and not TS_IGNORED.intersection(path.parts)}
    reverse: dict[str, set[str]] = {}
    for absolute, importer in candidates.items():
        try:
            content = absolute.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        for target in TS_IMPORT.findall(content):
            base = (absolute.parent / target).resolve()
            possible = [base, *[Path(str(base) + suffix) for suffix in TS_SUFFIXES],
                        *[base / ("index" + suffix) for suffix in TS_SUFFIXES]]
            for candidate in possible:
                if candidate in candidates:
                    reverse.setdefault(candidates[candidate], set()).add(importer)
                    break
    return {key: sorted(value) for key, value in reverse.items()}


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


def analyze(changed: list[str], inventory: dict, ts_reverse: dict[str, list[str]] | None = None) -> dict:
    indexed = {entry["path"]: entry for entry in inventory.get("files", [])}
    results = []
    for path in sorted(set(changed)):
        entry = indexed.get(path, {})
        importers = sorted(set(entry.get("imported_by", []) + (ts_reverse or {}).get(path, [])))
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
        "method": "audited Python import graph + literal relative TS/JS imports + cross-boundary hints",
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
    print(json.dumps(analyze(changed, inventory, typescript_edges(ROOT)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
