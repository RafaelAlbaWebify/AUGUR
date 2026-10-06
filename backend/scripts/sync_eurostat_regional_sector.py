from __future__ import annotations

import json

from app.db.bootstrap import initialize_datastores
from app.db.analytics import upsert_regional_sector_employment
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_sector import fetch_regional_sector_employment


def main() -> int:
    initialize_datastores()
    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        rows, diagnostic = fetch_regional_sector_employment(adapter)
    finally:
        adapter.close()

    inserted = upsert_regional_sector_employment(rows)
    print(json.dumps({
        "status": "complete" if inserted else "empty",
        "rows_parsed": len(rows),
        "rows_upserted": inserted,
        "region_count": len({row["geo_code"] for row in rows}),
        "country_prefixes": sorted({row["geo_code"][:2] for row in rows}),
        "nace_codes": sorted({row["nace_code"] for row in rows}),
        "latest_period": max((row["period"] for row in rows), default=None),
        "diagnostic": diagnostic,
    }, indent=2, default=str))
    return 0 if inserted else 2


if __name__ == "__main__":
    raise SystemExit(main())
