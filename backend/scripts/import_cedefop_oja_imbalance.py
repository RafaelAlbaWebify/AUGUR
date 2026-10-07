from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import settings
from app.db.bootstrap import initialize_datastores
from app.db.analytics import upsert_labour_oja_imbalance_eu27
from app.ingestion.cedefop_oja_imbalance import download_csv, parse_csv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import the official Cedefop EU27 OJA imbalance CSV."
    )
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()

    initialize_datastores()

    if args.input:
        path = args.input.expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Input CSV not found: {path}")
        download = None
    else:
        path = (
            settings.data_dir
            / "cache"
            / "cedefop-oja-imbalance-2026-05.csv"
        )
        download = download_csv(path)

    rows = parse_csv(path)
    inserted = upsert_labour_oja_imbalance_eu27(rows)

    print(json.dumps({
        "status": "complete" if inserted else "empty",
        "input": str(path),
        "rows_parsed": len(rows),
        "rows_upserted": inserted,
        "release_versions": sorted({row["release_version"] for row in rows}),
        "geographic_scope": "EU27",
        **({"download": download} if download is not None else {}),
    }, indent=2, default=str))
    return 0 if inserted else 2


if __name__ == "__main__":
    raise SystemExit(main())
