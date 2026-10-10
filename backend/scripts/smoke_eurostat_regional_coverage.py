"""Run a read-only live Eurostat regional coverage + GISCO NUTS 2024 smoke."""
import json

import httpx

from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_geography_discovery import discover_regional_dataset_coverage
from app.ingestion.eurostat_nuts_registry import (
    assess_reconciled_live_coverage,
    fetch_official_nuts2_codes,
    reconcile_nuts2024,
)
from app.ingestion.eurostat_regional_housing import REGIONAL_HOUSING_SERIES
from app.ingestion.eurostat_regional_labour import REGIONAL_LABOUR_SERIES


def main() -> int:
    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        report = discover_regional_dataset_coverage(
            adapter,
            REGIONAL_HOUSING_SERIES + REGIONAL_LABOUR_SERIES,
        )
    finally:
        adapter.close()

    with httpx.Client(
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        official_codes = fetch_official_nuts2_codes(client)

    reconciled = reconcile_nuts2024(report, official_codes)
    assessment = assess_reconciled_live_coverage(reconciled)
    print(json.dumps(assessment, indent=2))
    return 0 if assessment["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
