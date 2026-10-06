from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

from app.ingestion.cedefop_stas import (
    DATASET_PAGE_URL,
    download_workbook,
    inspect_workbook,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download and inspect the official Cedefop STAS workbook."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Inspect an existing local STAS XLSX instead of downloading it.",
    )
    parser.add_argument(
        "--url",
        help="Optional direct XLSX URL. By default AUGUR resolves it from the official dataset page.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data") / "cedefop" / "stas_latest.xlsx",
        help="Download destination when --input is not used.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=40,
        help="Maximum rows inspected per worksheet.",
    )
    args = parser.parse_args()

    if args.input:
        workbook = args.input
        download = None
    else:
        with httpx.Client(
            timeout=90,
            headers={"User-Agent": "AUGUR/0.1 Cedefop STAS evidence sync"},
        ) as client:
            download = download_workbook(
                client,
                args.output,
                download_url=args.url,
            )
        workbook = args.output

    diagnostic = inspect_workbook(workbook, max_rows=args.max_rows)
    payload = {
        "dataset_page": DATASET_PAGE_URL,
        "download": download,
        **diagnostic,
    }
    print(json.dumps(payload, indent=2, default=str))

    return 0 if diagnostic["ready_for_parser_implementation"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
