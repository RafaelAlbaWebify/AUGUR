from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import settings
from app.db.bootstrap import initialize_datastores
from app.db.analytics import upsert_labour_shortage_index
from app.ingestion.cedefop_clssi import (
    download_workbook,
    parse_workbook,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import the official Cedefop CLSSI workbook into AUGUR."
    )
    parser.add_argument(
        "--input",
        help="Existing CLSSI XLSX. If omitted, download the official workbook.",
    )
    args = parser.parse_args()

    initialize_datastores()

    if args.input:
        path = Path(args.input).expanduser().resolve()
        download = None
    else:
        path = settings.data_dir / "cache" / "cedefop_clssi_2026.xlsx"
        download = download_workbook(path)

    rows = parse_workbook(path)
    upserted = upsert_labour_shortage_index(rows)

    payload = {
        "status": "complete",
        "input": str(path),
        "rows_parsed": len(rows),
        "rows_upserted": upserted,
        "countries": sorted({row["country_iso3"] for row in rows}),
        "horizons": sorted({row["horizon"] for row in rows}),
        "isco_level": 2,
        "release_versions": sorted({row["release_version"] for row in rows}),
    }
    if download is not None:
        payload["download"] = download

    print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
