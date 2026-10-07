from __future__ import annotations

import json

from app.db.analytics import country_registry, geography_coverage_status
from app.db.bootstrap import initialize_datastores
from app.ingestion.oecd_regional import OECDRegionalAdapter


def main() -> int:
    initialize_datastores()

    target_countries = {
        country["iso3"]
        for country in country_registry()
        if country.get("oecd_member")
        and not country.get("eu_member")
    }

    if not target_countries:
        print(json.dumps({
            "source_id": "OECD",
            "dataset_id": "DSD_REG_DEMO@DF_DENSITY",
            "status": "no_registered_non_eu_oecd_countries",
            "rows": 0,
        }, indent=2))
        return 0

    adapter = OECDRegionalAdapter(
        timeout_seconds=180,
        max_retries=3,
    )
    try:
        result = adapter.sync_density(
            allowed_country_iso3=target_countries,
            start_year=2021,
        )
    finally:
        adapter.close()

    payload = {
        **result,
        "target_country_count": len(target_countries),
        "target_countries": sorted(target_countries),
        "geography_coverage": geography_coverage_status(),
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if result["rows"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
