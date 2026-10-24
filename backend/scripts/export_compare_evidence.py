"""Read-only evidence export matching the national compare selection order.

Usage from backend: python -m scripts.export_compare_evidence --output comparison_evidence.json
Reads national aggregate observations only. Never initializes or modifies DuckDB.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import duckdb
from app.core.config import settings

COUNTRIES = ("ESP", "IRL")


def collect(path: Path) -> dict:
    con = duckdb.connect(str(path), read_only=True)
    try:
        result = con.execute("""
            WITH ranked AS (
                SELECT o.country_iso3, o.indicator_id, i.name, i.dimension,
                    o.period, o.value, o.unit, o.source_id, o.dataset_id,
                    o.observation_type, o.retrieved_at, o.source_updated_at,
                    o.source_observation_status, o.source_decimal,
                    ROW_NUMBER() OVER (
                        PARTITION BY o.country_iso3, o.indicator_id
                        ORDER BY o.period DESC, s.priority ASC, o.source_id ASC
                    ) AS rn
                FROM observations o
                JOIN indicators i USING (indicator_id)
                JOIN sources s USING (source_id)
                WHERE o.country_iso3 IN ('ESP','IRL')
                  AND o.observation_type = 'observed'
            )
            SELECT country_iso3, indicator_id, name, dimension, period,
                value, unit, source_id, dataset_id, observation_type,
                retrieved_at, source_updated_at, source_observation_status,
                source_decimal
            FROM ranked WHERE rn = 1
            ORDER BY dimension, indicator_id, country_iso3
        """)
        names = [col[0] for col in result.description]
        rows = [dict(zip(names, values)) for values in result.fetchall()]
        for row in rows:
            row["retrieved_at"] = (row["retrieved_at"].isoformat()
                                   if row["retrieved_at"] is not None else None)
        country_counts = {code: sum(row["country_iso3"] == code for row in rows)
                          for code in COUNTRIES}
        return {"scope": "national_latest_observed_exact_compare_selection",
                "countries": list(COUNTRIES), "country_counts": country_counts,
                "rows": rows, "read_only": True,
                "limitations": [
                    "Current selected row only, not full history or source publication vintage",
                    "Observation source_updated_at and retrieved_at are not interchangeable",
                    "Dataset ID does not itself prove unit or methodological comparability",
                ]}
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.suffix.lower() != ".json":
        parser.error("Output must be a JSON file")
    if not settings.duckdb_path.is_file():
        parser.error("Analytical DuckDB missing; no database was initialized")
    report = collect(settings.duckdb_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "country_counts": report["country_counts"],
                      "rows": len(report["rows"]), "read_only": True}))


if __name__ == "__main__":
    main()
