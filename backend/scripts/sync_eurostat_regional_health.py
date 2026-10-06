from __future__ import annotations

import json

from app.db.bootstrap import initialize_datastores
from app.db.analytics import upsert_subnational_observations
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_health import fetch_regional_health_evidence


def main() -> int:
    initialize_datastores()
    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        rows, diagnostics = fetch_regional_health_evidence(adapter)
    finally:
        adapter.close()

    inserted = upsert_subnational_observations(rows)
    print(json.dumps({
        "status": "complete" if inserted else "empty",
        "rows_parsed": len(rows),
        "rows_upserted": inserted,
        "region_count": len({row["geo_code"] for row in rows}),
        "country_prefixes": sorted({row["geo_code"][:2] for row in rows}),
        "indicator_ids": sorted({row["indicator_id"] for row in rows}),
        "latest_period": max((row["period"] for row in rows), default=None),
        "diagnostics": diagnostics,
        "coverage_note": "Regional unmet-needs coverage may be unavailable for countries reporting only national data.",
    }, indent=2, default=str))
    return 0 if inserted else 2


if __name__ == "__main__":
    raise SystemExit(main())
