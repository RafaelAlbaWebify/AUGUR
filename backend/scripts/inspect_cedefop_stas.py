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
        if not workbook.exists():
            print(json.dumps({
                "status": "input_file_missing",
                "input": str(workbook),
                "next_action": "Download the current STAS XLSX from the official Cedefop dataset page and pass its local path with --input.",
            }, indent=2))
            return 2
    else:
        try:
            with httpx.Client(
                timeout=90,
                headers={
                    "User-Agent": "Mozilla/5.0 AUGUR-STAS-Inspector/0.1",
                    "Accept": "text/html,application/xhtml+xml,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            ) as client:
                download = download_workbook(
                    client,
                    args.output,
                    download_url=args.url,
                )
            workbook = args.output
        except (httpx.HTTPError, RuntimeError) as exc:
            print(json.dumps({
                "status": "manual_download_required",
                "dataset_page": DATASET_PAGE_URL,
                "error": str(exc),
                "next_action": (
                    "Open the official STAS dataset page in a browser, download the current XLSX, "
                    "then run .\\inspect-cedefop-stas.ps1 --input <local-xlsx-path>."
                ),
            }, indent=2))
            return 2

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
