from __future__ import annotations

import json

from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_health import inspect_regional_health_sources


def main() -> int:
    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        result = inspect_regional_health_sources(adapter)
    finally:
        adapter.close()

    print(json.dumps(result, indent=2, default=str))
    return 0 if result["ready_for_parser_design"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
