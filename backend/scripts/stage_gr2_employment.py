"""Construct an isolated GR-2 employment correction rehearsal; never write source DB.

From backend/: python -m scripts.stage_gr2_employment --output PATH.duckdb --report PATH.json

The output path MUST NOT already exist. This is NOT a certified ranking release.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import duckdb
from app.core.config import settings
from app.ingestion.eurostat import EurostatAdapter
from app.services.regional_evidence import REGIONAL_INDICATORS
from app.services.ranking_provider_metadata import check_provider_metadata

PERIOD = 2025
INDICATOR = "regional_employment_rate"
SYSTEM = "NUTS_2024"


def fingerprint(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stage(source_path: Path, output_path: Path, adapter: EurostatAdapter) -> dict:
    source_path = source_path.resolve()
    output_path = output_path.resolve()
    if output_path == source_path:
        raise ValueError("Staging destination equals production/source database")
    if output_path.exists():
        raise FileExistsError("Staging destination must not already exist")
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if Path(str(source_path) + ".wal").exists():
        raise RuntimeError("Source DuckDB has WAL; close AUGUR and checkpoint before copying")
    before = fingerprint(source_path)
    conn = duckdb.connect(str(source_path), read_only=True)
    try:
        rows = conn.execute(
            """SELECT DISTINCT s.geo_code, g.country_iso3
               FROM subnational_observations s
               JOIN geography_registry g ON
                    g.source_geo_code=s.geo_code
                AND g.geography_system=s.geography_system
                AND LOWER(g.geo_level)=LOWER(s.geo_level)
               WHERE s.indicator_id=? AND s.period=? AND s.geography_system=?
                 AND g.country_iso3 IN ('ESP','PRT','IRL')
               ORDER BY s.geo_code""",
            [INDICATOR, PERIOD, SYSTEM],
        ).fetchall()
        source_count = conn.execute(
            """SELECT count(*) FROM subnational_observations WHERE
               indicator_id=? AND period=? AND geography_system=?""",
            [INDICATOR, PERIOD, SYSTEM],
        ).fetchone()[0]
        if not rows or len(rows) != source_count:
            raise ValueError("Local employment source is missing or has duplicated/unregistered regions")
        config = next(x for x in REGIONAL_INDICATORS if x["indicator_id"] == INDICATOR)
        new = {}
        by_country = {}
        for geo, country in rows:
            by_country.setdefault(country, []).append(geo)
        for country, codes in sorted(by_country.items()):
            filters = {**config["filters"], "geo": codes, "time": str(PERIOD)}
            payload = adapter.fetch_dataset(config["dataset_id"], filters)
            observations = adapter.normalize(country, {
                "indicator_id": INDICATOR, "dataset_id": config["dataset_id"],
                "unit": config["unit"], "dimension_values": {k: v for k, v in filters.items() if k != "geo"},
            }, payload)
            for row in observations:
                dims = row.get("source_dimensions") or {}
                geo = dims.get("geo")
                if geo not in codes or row.get("period") != PERIOD:
                    continue
                problems = check_provider_metadata(
                    json.dumps(dims), row.get("source_observation_status"),
                    geo_code=geo, period=PERIOD, indicator_id=INDICATOR,
                )
                if any(reason != "provider_status_review_required" for reason in problems):
                    raise ValueError(f"Provider dimension mismatch for {geo}")
                if geo in new:
                    raise ValueError(f"Duplicate exact-cohort source observation for {geo}")
                new[geo] = row
        if set(new) != {code for code, _ in rows}:
            missing = sorted({code for code, _ in rows} - set(new))
            extra = sorted(set(new) - {code for code, _ in rows})
            raise ValueError(f"Provider source missing exact-cohort observations: missing={missing}, unexpected={extra}")
    finally:
        conn.close()
    if fingerprint(source_path) != before or Path(str(source_path) + ".wal").exists():
        raise RuntimeError("Source DuckDB changed during staged retrieval; do not copy")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        # Never open a writable connection to source. Stage is a new, exclusive path.
        with source_path.open("rb") as src, output_path.open("xb") as dst:
            created = True
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        if fingerprint(output_path) != before or fingerprint(source_path) != before:
            raise RuntimeError("Staging copy does not match original fingerprint")
        con = duckdb.connect(str(output_path), read_only=False)
        try:
            con.execute("BEGIN TRANSACTION")
            con.execute("""CREATE TABLE gr2_remediation_before AS
                SELECT * FROM subnational_observations
                WHERE indicator_id=? AND period=? AND geography_system=?""",
                [INDICATOR, PERIOD, SYSTEM])
            cols = {r[1] for r in con.execute("PRAGMA table_info('subnational_observations')").fetchall()}
            for col in ("request_filters_json", "response_dimensions_json", "source_observation_status"):
                if col not in cols:
                    con.execute(f"ALTER TABLE subnational_observations ADD COLUMN {col} VARCHAR")
            effects = []
            flagged = Counter()
            for geo, country in rows:
                row = new[geo]
                dimensions = row["source_dimensions"]
                status = row.get("source_observation_status")
                if status:
                    flagged[str(status)] += 1
                old = con.execute("""SELECT value FROM subnational_observations
                   WHERE geography_system=? AND geo_code=? AND indicator_id=? AND period=?""",
                   [SYSTEM, geo, INDICATOR, PERIOD]).fetchone()[0]
                count = con.execute("""UPDATE subnational_observations SET
                   value=?, request_filters_json=?, response_dimensions_json=?,
                   source_observation_status=?, source_updated_at=?
                   WHERE geography_system=? AND geo_code=? AND indicator_id=? AND period=?""",
                   [float(row["value"]),
                    json.dumps({**config["filters"], "geo": geo, "time": str(PERIOD)}, sort_keys=True),
                    json.dumps(dimensions, sort_keys=True),
                    status, row.get("source_updated_at"),
                    SYSTEM, geo, INDICATOR, PERIOD])
                effects.append({"geo_code": geo, "country_iso3": country,
                                "old_value": float(old), "staged_value": float(row["value"]),
                                "source_status": status})
            staged_count = con.execute("""SELECT count(*) FROM subnational_observations
                WHERE indicator_id=? AND period=? AND geography_system=?""",
                [INDICATOR, PERIOD, SYSTEM]).fetchone()[0]
            if staged_count != source_count:
                raise ValueError("Staged record count changed")
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        finally:
            con.close()
        if fingerprint(source_path) != before:
            raise RuntimeError("Original database changed while staging")
        return {"status": "isolated_rehearsal_not_source_or_vintage_certification",
                "source_sha256": before, "source_unchanged": True,
                "staged_path": str(output_path), "changed_rows": len(effects),
                "flag_counts": dict(sorted(flagged.items())),
                "source_quality_gate": "blocked_pending_official_policy",
                "boundary_vintage_gate": "blocked_unverified",
                "production_writes": 0, "changes": effects}
    except Exception:
        if created and output_path.exists():
            output_path.unlink()
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.output.resolve() == args.report.resolve():
        parser.error("Output DB and report paths must differ")
    adapter = EurostatAdapter(timeout_seconds=90, max_retries=2)
    try:
        result = stage(settings.duckdb_path, args.output, adapter)
    finally:
        adapter.close()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "changed_rows": result["changed_rows"],
                      "production_writes": 0, "report": str(args.report)}))


if __name__ == "__main__":
    main()
