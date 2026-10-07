from __future__ import annotations

import json

from app.db.bootstrap import initialize_datastores
from app.ingestion.world_bank import WorldBankAdapter
from app.services.country import country_coverage_summary


def main() -> int:
    initialize_datastores()

    adapter = WorldBankAdapter(timeout_seconds=90, max_retries=3)
    try:
        countries = adapter.register_country_catalog()
    finally:
        adapter.close()

    coverage = country_coverage_summary()
    payload = {
        "source_id": "WORLD_BANK",
        "registered_from_source": len(countries),
        "registered_country_count": coverage["registered_country_count"],
        "analyzable_country_count": coverage["analyzable_country_count"],
        "validation_country_count": coverage["validation_country_count"],
    }
    print(json.dumps(payload, indent=2))
    return 0 if countries else 2


if __name__ == "__main__":
    raise SystemExit(main())
