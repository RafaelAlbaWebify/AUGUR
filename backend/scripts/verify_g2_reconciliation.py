"""Read-only exact comparison of original and G2-reconciled AUGUR DuckDB files.

No database mutations. The only allowed differences:
- 172 original NUTS_2024 observation rows for five obsolete codes relabelled
  NUTS_UNSPECIFIED, with every other column unchanged.
- Five corresponding NUTS_2024 geographic registry rows removed.
Every other table and every other observation must match as a multiset.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import duckdb

CODES = ("IE01", "IE02", "PT16", "PT17", "PT18")
EXPECTED_OBSERVATIONS = 172
EXPECTED_REGISTRY = 5


def read_database(path: Path) -> tuple[dict, dict, dict]:
    if not path.is_file():
        raise FileNotFoundError(path)
    con = duckdb.connect(str(path), read_only=True)
    try:
        schemas = {}
        tables = {}
        for (name,) in con.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='main' AND table_type='BASE TABLE'
            ORDER BY table_name
        """).fetchall():
            # Table names originate from the DB catalog, not user CLI input.
            escaped = name.replace('"', '""')
            result = con.execute(f'SELECT * FROM "{escaped}"')
            schemas[name] = tuple((col[0], str(col[1])) for col in result.description)
            tables[name] = Counter(tuple(row) for row in result.fetchall())
        checks = con.execute("PRAGMA database_size").fetchall()
        return schemas, tables, {"database_size": str(checks[0]) if checks else "unknown"}
    finally:
        con.close()


def validate(original: Path, reconciled: Path) -> dict:
    if original.resolve() == reconciled.resolve():
        raise ValueError("Both paths resolve to the same file")
    schema_a, a, _ = read_database(original)
    schema_b, b, _ = read_database(reconciled)
    failures = []
    if schema_a != schema_b:
        failures.append("Table/column schemas differ")
    for table in sorted(set(a) | set(b)):
        if table in {"subnational_observations", "geography_registry"}:
            continue
        if a.get(table) != b.get(table):
            failures.append(f"Unanticipated difference in table {table}")

    obs = "subnational_observations"
    reg = "geography_registry"
    if obs not in a or obs not in b or reg not in a or reg not in b:
        failures.append("Required comparison tables missing")
        return {"passed": False, "failures": failures}
    fields = [name for name, _ in schema_a[obs]]
    gidx, cidx = fields.index("geography_system"), fields.index("geo_code")
    old = Counter()
    transformed = Counter()
    for row, n in a[obs].items():
        if row[gidx] == "NUTS_2024" and row[cidx] in CODES:
            old[row] += n
            newrow = list(row)
            newrow[gidx] = "NUTS_UNSPECIFIED"
            transformed[tuple(newrow)] += n
        else:
            transformed[row] += n
    if sum(old.values()) != EXPECTED_OBSERVATIONS:
        failures.append(f"Expected 172 original targeted observations; found {sum(old.values())}")
    if transformed != b[obs]:
        failures.append("Observation content differs beyond the 172 approved vintage relabels")

    registry_fields = [name for name, _ in schema_a[reg]]
    ididx = registry_fields.index("geo_id")
    sysidx = registry_fields.index("geography_system")
    expected_ids = {f"NUTS_2024:{code}" for code in CODES}
    removed = Counter()
    expected_registry = Counter()
    for row, n in a[reg].items():
        if row[ididx] in expected_ids and row[sysidx] == "NUTS_2024":
            removed[row] += n
        else:
            expected_registry[row] += n
    if {row[ididx] for row in removed} != expected_ids or sum(removed.values()) != EXPECTED_REGISTRY:
        failures.append("Original registry targets do not match exactly five approved IDs")
    if expected_registry != b[reg]:
        failures.append("Registry differs beyond five approved retired-code removals")

    return {
        "passed": not failures,
        "table_count": len(a),
        "original_observations": sum(a[obs].values()),
        "reconciled_observations": sum(b[obs].values()),
        "observation_rows_relabelled": sum(old.values()),
        "registry_rows_removed": sum(removed.values()),
        "codes": list(CODES),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--reconciled", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.original, args.reconciled)
    print(json.dumps(result, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
