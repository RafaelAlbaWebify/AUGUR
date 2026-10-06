from __future__ import annotations

import json

from app.ingestion.eurostat import EurostatAdapter
from app.services.regional_evidence import regional_evidence


TARGETS = ["ES120", "PT170", "IE061"]


def main() -> int:
    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        results = [regional_evidence(code, adapter=adapter) for code in TARGETS]
    finally:
        adapter.close()

    ok = all(item.get("available_count", 0) > 0 for item in results)
    print(json.dumps({
        "status": "available" if ok else "partial",
        "targets": results,
    }, indent=2, default=str))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
