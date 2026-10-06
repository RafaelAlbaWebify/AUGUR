from __future__ import annotations

import argparse
import json

from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_jvs import (
    REFERENCE_PERIOD,
    inspect_regional_jvs,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Eurostat NUTS2/occupation quarterly JVS coverage."
    )
    parser.add_argument(
        "--period",
        default=REFERENCE_PERIOD,
        help="Quarter to inspect, default: 2026-Q2.",
    )
    args = parser.parse_args()

    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        result = inspect_regional_jvs(adapter, args.period)
    finally:
        adapter.close()

    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("ready_for_parser_implementation") else 2


if __name__ == "__main__":
    raise SystemExit(main())
