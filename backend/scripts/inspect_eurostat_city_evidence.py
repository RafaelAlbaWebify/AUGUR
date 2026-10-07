from __future__ import annotations

import json

from app.ingestion.eurostat import EurostatAdapter
from app.services.city_evidence import CITY_INDICATORS, _fetch_city_indicators


PROBE_CITY = "ES013C"


def main() -> int:
    adapter = EurostatAdapter(timeout_seconds=60.0, max_retries=2)
    try:
        indicators = _fetch_city_indicators(adapter, PROBE_CITY)

        population_config = next(
            item
            for item in CITY_INDICATORS
            if item["indicator_id"] == "city_population"
        )
        batch_codes = ["ES001C", PROBE_CITY]
        batch_payload = adapter.fetch_dataset(
            population_config["dataset_id"],
            {
                "cities": batch_codes,
                "freq": "A",
            },
        )
        batch_population = {}
        for city_code in batch_codes:
            rows = adapter.normalize(
                city_code,
                {
                    "indicator_id": population_config["indicator_id"],
                    "dataset_id": population_config["dataset_id"],
                    "unit": population_config["unit"],
                    "dimension_values": {
                        "cities": city_code,
                        "indic_ur": population_config["indic_ur"],
                    },
                },
                batch_payload,
            )
            batch_population[city_code] = rows
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
        "batch_population_probe": {
            city_code: {
                "row_count": len(rows),
                "latest_period": max((row["period"] for row in rows), default=None),
                "latest_value": (
                    max(rows, key=lambda row: row["period"])["value"]
                    if rows
                    else None
                ),
            }
            for city_code, rows in batch_population.items()
        },
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
    if any(not rows for rows in batch_population.values()):
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
