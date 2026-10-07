from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import settings
from app.ingestion.cedefop_clssi import (
    download_workbook,
    inspect_workbook,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download/inspect the official Cedefop CLSSI workbook "
            "without writing analytical data."
        )
    )
    parser.add_argument(
        "--input",
        help="Existing local CLSSI XLSX. If omitted, download the official workbook.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=80,
    )
    args = parser.parse_args()

    if args.input:
        path = Path(args.input).expanduser().resolve()
        download = None
    else:
        path = (
            settings.data_dir
            / "cache"
            / "cedefop_clssi_2026.xlsx"
        )
        download = download_workbook(path)

    result = inspect_workbook(
        path,
        max_rows=args.max_rows,
    )
    if download is not None:
        result["download"] = download

    print(json.dumps(result, indent=2, default=str))
    return (
        0
        if result["ready_for_parser_implementation"]
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
