from __future__ import annotations

import json

from app.db.bootstrap import initialize_datastores
from app.db.analytics import (
    regional_sector_employment_status,
    upsert_regional_sector_employment,
)
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_sector import (
    fetch_regional_sector_employment,
)


def ensure_regional_sector_evidence() -> dict:
    before = regional_sector_employment_status()
    if before.get("available"):
        return {
            "evidence_id": "regional_sector_employment",
            "status": "available",
            "action": "none",
            "before": before,
            "after": before,
        }

    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        rows, diagnostic = fetch_regional_sector_employment(adapter)
    finally:
        adapter.close()

    rows_upserted = upsert_regional_sector_employment(rows)
    after = regional_sector_employment_status()

    return {
        "evidence_id": "regional_sector_employment",
        "status": "available" if after.get("available") else "missing",
        "action": "repaired" if after.get("available") else "repair_failed",
        "rows_parsed": len(rows),
        "rows_upserted": rows_upserted,
        "diagnostic": diagnostic,
        "before": before,
        "after": after,
    }


def main() -> int:
    initialize_datastores()

    results = [
        ensure_regional_sector_evidence(),
    ]
    repaired = [
        item["evidence_id"]
        for item in results
        if item["action"] == "repaired"
    ]
    failed = [
        item["evidence_id"]
        for item in results
        if item["status"] != "available"
    ]

    payload = {
        "status": "complete" if not failed else "partial",
        "repaired": repaired,
        "failed": failed,
        "results": results,
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
