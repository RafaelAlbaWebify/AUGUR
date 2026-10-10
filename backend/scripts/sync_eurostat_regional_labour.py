from __future__ import annotations

import json

from app.db.bootstrap import initialize_datastores
from app.ingestion.eurostat_regional_contract import validate_eurostat_regional_rows
from app.db.analytics import upsert_subnational_observations
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_labour import fetch_regional_labour, REGIONAL_LABOUR_SERIES


def main() -> int:
    initialize_datastores()
    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        rows, diagnostics = fetch_regional_labour(adapter)
    finally:
        adapter.close()

    validate_eurostat_regional_rows(rows, allowed_indicators={c["indicator_id"] for c in REGIONAL_LABOUR_SERIES})
    inserted = upsert_subnational_observations(rows)
    payload = {
        "status": "complete" if inserted else "empty",
        "rows_parsed": len(rows),
        "rows_upserted": inserted,
        "region_count": len({row["geo_code"] for row in rows}),
        "country_prefixes": sorted({row["geo_code"][:2] for row in rows}),
        "indicator_ids": sorted({row["indicator_id"] for row in rows}),
        "latest_period": max((row["period"] for row in rows), default=None),
        "diagnostics": diagnostics,
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if inserted else 2


if __name__ == "__main__":
    raise SystemExit(main())
