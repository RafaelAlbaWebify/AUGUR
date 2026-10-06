from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.db.bootstrap import initialize_datastores
from app.db.analytics import upsert_labour_occupation_outlook
from app.ingestion.cedefop_stas import parse_stas_workbook


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import an official Cedefop STAS XLSX into AUGUR."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the official STAS XLSX file.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input workbook not found: {args.input}")

    initialize_datastores()
    rows = parse_stas_workbook(args.input)
    inserted = upsert_labour_occupation_outlook(rows)

    summary = {
        "status": "complete" if inserted else "empty",
        "input": str(args.input),
        "rows_parsed": len(rows),
        "rows_upserted": inserted,
        "countries": sorted({row["country_iso3"] for row in rows}),
        "periods": sorted({row["period"] for row in rows}),
        "isco_levels": sorted({row["isco_level"] for row in rows}),
        "release_versions": sorted({row["release_version"] for row in rows}),
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0 if inserted else 2


if __name__ == "__main__":
    raise SystemExit(main())
