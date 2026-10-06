from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.ingestion.cedefop_oja_imbalance import inspect_csv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the official Cedefop OJA occupational-imbalance CSV."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=20)
    args = parser.parse_args()

    if not args.input.exists():
        print(json.dumps({
            "status": "input_file_missing",
            "input": str(args.input),
            "next_action": "Download cedefop-oja-imbalance-2026-05.csv from the official Cedefop dataset page and pass it with --input.",
        }, indent=2))
        return 2

    result = inspect_csv(args.input, max_rows=args.max_rows)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["ready_for_parser_implementation"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
