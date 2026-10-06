from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.db.bootstrap import initialize_datastores
from app.db.analytics import upsert_labour_oja_imbalance_eu27
from app.ingestion.cedefop_oja_imbalance import parse_csv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import the official Cedefop EU27 OJA imbalance CSV."
    )
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input CSV not found: {args.input}")

    initialize_datastores()
    rows = parse_csv(args.input)
    inserted = upsert_labour_oja_imbalance_eu27(rows)

    print(json.dumps({
        "status": "complete" if inserted else "empty",
        "input": str(args.input),
        "rows_parsed": len(rows),
        "rows_upserted": inserted,
        "release_versions": sorted({row["release_version"] for row in rows}),
        "geographic_scope": "EU27",
    }, indent=2, default=str))
    return 0 if inserted else 2


if __name__ == "__main__":
    raise SystemExit(main())
