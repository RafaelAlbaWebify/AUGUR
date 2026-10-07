from __future__ import annotations

import json

from app.ingestion.eurostat import EurostatAdapter
from app.services.city_evidence import CITY_INDICATORS, _fetch_city_indicators


PROBE_CITY = "ES013C"


def main() -> int:
    adapter = EurostatAdapter(timeout_seconds=60.0, max_retries=2)
    try:
        indicators = _fetch_city_indicators(adapter, PROBE_CITY)
    finally:
        adapter.close()

    available = [
        item for item in indicators
        if item.get("status") == "available"
    ]
    unavailable = [
        item for item in indicators
        if item.get("status") != "available"
    ]

    payload = {
        "city_code": PROBE_CITY,
        "configured_indicator_count": len(CITY_INDICATORS),
        "available_count": len(available),
        "available": [
            {
                "indicator_id": item["indicator_id"],
                "period": item.get("period"),
                "value": item.get("value"),
                "unit": item.get("unit"),
                "dataset_id": item.get("dataset_id"),
            }
            for item in available
        ],
        "unavailable": [
            {
                "indicator_id": item["indicator_id"],
                "dataset_id": item.get("dataset_id"),
                "reason": item.get("reason"),
            }
            for item in unavailable
        ],
    }
    print(json.dumps(payload, indent=2, default=str))

    population = next(
        (
            item for item in available
            if item["indicator_id"] == "city_population"
        ),
        None,
    )
    expanded = [
        item for item in available
        if item["indicator_id"] != "city_population"
    ]

    if population is None:
        return 2
    if not expanded:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
