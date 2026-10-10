"""Reconcile demonstrably invalid legacy NUTS_2024 labels in a *copy*.

Default action is an evidence-checked dry run. --output-db produces a new
DuckDB file; the source database is never opened read/write or replaced.
Current-code-but-vintage-unverified observations are not touched.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import duckdb

from app.core.config import settings
from scripts.audit_legacy_nuts_vintage import (
    classify_claims,
    fetch_official_codes,
    load_local_claims,
)

TARGET_SYSTEM = "NUTS_UNSPECIFIED"
SOURCE_SYSTEM = "NUTS_2024"


def _keys(rows: list[dict], fields: tuple[str, ...]) -> set[tuple]:
    return {tuple(row[field] for field in fields) for row in rows}


def preflight(source: Path, report: dict, official: dict[str, set[str]]) -> dict:
    if report.get("scope") != "legacy_local_nuts2024_vintage_audit" or report.get("mutation_performed") is not False:
        raise ValueError("Expected an unmodified legacy local NUTS audit report")
    observations, registry = load_local_claims(source)
    current = classify_claims(official, observations, registry)
    expected_obs = report.get("definite_observation_mislabels")
    expected_registry = report.get("invalid_current_registry_rows")
    if not isinstance(expected_obs, list) or not isinstance(expected_registry, list):
        raise ValueError("Audit report lacks definite observation and registry rows")
    # Include counts/period boundaries in the audit snapshot check; do not
    # operate on a database that has changed since the supplied report.
    obs_fields = ("geo_level", "geo_code", "source_id", "dataset_id",
                  "first_period", "last_period", "observation_count")
    registry_fields = ("geo_id", "geo_level", "source_geo_code",
                       "country_iso2", "source_id")
    if _keys(current["definite_observation_mislabels"], obs_fields) != _keys(expected_obs, obs_fields):
        raise ValueError("Observation audit no longer matches the source database")
    if _keys(current["invalid_current_registry_rows"], registry_fields) != _keys(expected_registry, registry_fields):
        raise ValueError("Registry audit no longer matches the source database")

    bad = current["definite_observation_mislabels"]
    invalid = current["invalid_current_registry_rows"]
    if not bad and not invalid:
        return {"observation_rows": 0, "registry_rows": 0, "codes": []}
    codes = sorted({r["geo_code"] for r in bad} | {r["source_geo_code"] for r in invalid})
    for row in bad:
        if row["geo_code"] in official[row["geo_level"]]:
            raise ValueError("Target is current GISCO territory: refusal")
    for row in invalid:
        if row["source_geo_code"] in official[row["geo_level"]]:
            raise ValueError("Target is current GISCO registry row: refusal")

    con = duckdb.connect(str(source), read_only=True)
    try:
        # Key of subnational observations includes geography_system, geo_code,
        # indicator_id, period, source_id. Updating can therefore collide with
        # an already-ingested NUTS_UNSPECIFIED record.
        collisions = con.execute("""
            SELECT COUNT(*) FROM subnational_observations legacy
            JOIN subnational_observations target
              ON target.geography_system = ?
             AND target.geo_code = legacy.geo_code
             AND target.indicator_id = legacy.indicator_id
             AND target.period = legacy.period
             AND target.source_id = legacy.source_id
            WHERE legacy.geography_system = ?
              AND legacy.geo_code IN (SELECT UNNEST(?))
        """, [TARGET_SYSTEM, SOURCE_SYSTEM, codes]).fetchone()[0]
        if collisions:
            raise ValueError(f"Refusing {collisions} duplicate primary-key collision(s)")
        count = con.execute("""
            SELECT COUNT(*) FROM subnational_observations
            WHERE geography_system = ? AND geo_code IN (SELECT UNNEST(?))
        """, [SOURCE_SYSTEM, codes]).fetchone()[0]
        expected_count = sum(int(r["observation_count"]) for r in bad)
        if count != expected_count:
            raise ValueError(f"Unexpected target row count {count} != {expected_count}")
        ids = [r["geo_id"] for r in invalid]
        registry_count = con.execute("""
            SELECT COUNT(*) FROM geography_registry WHERE geo_id IN (SELECT UNNEST(?))
        """, [ids]).fetchone()[0]
        if registry_count != len(ids):
            raise ValueError("Catalog changed since audit")
        return {"observation_rows": count, "registry_rows": registry_count, "codes": codes}
    finally:
        con.close()


def reconcile_copy(source: Path, output: Path, plan: dict) -> dict:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing database: {output}")
    if source.resolve() == output.resolve():
        raise ValueError("Source and output database paths must differ")
    output.parent.mkdir(parents=True, exist_ok=True)
    # No in-place writes. A live writer should be stopped so the file-level
    # snapshot is consistent; open/lock problems fail before any source change.
    shutil.copy2(source, output)
    codes = plan["codes"]
    con = None
    try:
        con = duckdb.connect(str(output))
        con.execute("BEGIN TRANSACTION")
        before_total = con.execute("SELECT COUNT(*) FROM subnational_observations").fetchone()[0]
        before_registry = con.execute("SELECT COUNT(*) FROM geography_registry").fetchone()[0]
        changed = con.execute("""
            UPDATE subnational_observations
               SET geography_system = ?
             WHERE geography_system = ? AND geo_code IN (SELECT UNNEST(?))
            RETURNING geo_code
        """, [TARGET_SYSTEM, SOURCE_SYSTEM, codes]).fetchall()
        if len(changed) != plan["observation_rows"]:
            raise ValueError("Changed observation count differs from preflight")
        invalid_ids = [f"{SOURCE_SYSTEM}:{code}" for code in codes]
        removed = con.execute("""
            DELETE FROM geography_registry
             WHERE geo_id IN (SELECT UNNEST(?))
               AND geography_system = ?
            RETURNING geo_id
        """, [invalid_ids, SOURCE_SYSTEM]).fetchall()
        if len(removed) != plan["registry_rows"]:
            raise ValueError("Removed registry count differs from preflight")
        after_total = con.execute("SELECT COUNT(*) FROM subnational_observations").fetchone()[0]
        after_registry = con.execute("SELECT COUNT(*) FROM geography_registry").fetchone()[0]
        if before_total != after_total or before_registry - after_registry != len(removed):
            raise ValueError("Preservation invariant failed")
        remaining = con.execute("""
            SELECT COUNT(*) FROM subnational_observations
             WHERE geography_system = ? AND geo_code IN (SELECT UNNEST(?))
        """, [SOURCE_SYSTEM, codes]).fetchone()[0]
        if remaining:
            raise ValueError("Invalid NUTS_2024 observation claims remain")
        con.execute("COMMIT")
        return {"output_database": str(output), "observation_rows_relabelled": len(changed),
                "registry_rows_removed_from_current": len(removed),
                "total_observations_preserved": after_total}
    except Exception:
        if con is not None:
            try:
                con.execute("ROLLBACK")
            except Exception:
                pass
        raise
    finally:
        if con is not None:
            con.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--source-db", type=Path, default=Path(settings.duckdb_path))
    parser.add_argument("--output-db", type=Path, help="Create a reconciled COPY; never modify the source")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    official = fetch_official_codes()
    plan = preflight(args.source_db, report, official)
    print(json.dumps({"action": "dry_run", **plan}, indent=2))
    if args.output_db is not None:
        result = reconcile_copy(args.source_db, args.output_db, plan)
        print(json.dumps({"action": "copy_created", **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
