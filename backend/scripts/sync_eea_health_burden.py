from __future__ import annotations

import json

from app.catalog import COUNTRIES
from app.db.analytics import (
    environmental_health_burden_status,
    upsert_environmental_health_burden,
)
from app.db.bootstrap import initialize_datastores
from app.ingestion.eea_health_burden import fetch_eea_pm25_burden_evidence


def main() -> int:
    initialize_datastores()
    prefixes = {
        country["iso2"]
        for country in COUNTRIES
        if country.get("eu_member")
    }

    rows, diagnostic = fetch_eea_pm25_burden_evidence(
        country_prefixes=prefixes,
    )
    inserted = upsert_environmental_health_burden(rows)
    status = environmental_health_burden_status()

    print(json.dumps({
        "status": "complete" if inserted else "empty",
        "rows_parsed": len(rows),
        "rows_upserted": inserted,
        "diagnostic": diagnostic,
        "storage": status,
        "scope_note": (
            "PM2.5 attributable health burden is stored separately from "
            "observed city PM2.5 concentration."
        ),
    }, indent=2, default=str))

    return 0 if inserted else 2


if __name__ == "__main__":
    raise SystemExit(main())
