from __future__ import annotations

from app.ingestion.eurostat import EurostatAdapter


CITY_POPULATION = {
    "indicator_id": "city_population",
    "name": "Population",
    "dataset_id": "urb_cpop1",
    "filters": {
        "freq": "A",
        "indic_ur": "DE1001V",
    },
    "unit": "persons",
}


def city_evidence(
    city_code: str,
    adapter: EurostatAdapter | None = None,
) -> dict:
    code = city_code.strip().upper()
    owns_adapter = adapter is None
    active_adapter = adapter or EurostatAdapter(timeout_seconds=20.0, max_retries=2)

    try:
        try:
            payload = active_adapter.fetch_dataset(
                CITY_POPULATION["dataset_id"],
                {
                    "cities": code,
                    **CITY_POPULATION["filters"],
                },
            )
            rows = active_adapter.normalize(
                code,
                CITY_POPULATION,
                payload,
            )
        except Exception as exc:
            return {
                "city_code": code,
                "geo_level": "city",
                "source": "Eurostat City Statistics / Urban Audit",
                "minimum_population_scope": 50000,
                "indicator_count": 1,
                "available_count": 0,
                "complete": False,
                "indicators": [{
                    "indicator_id": CITY_POPULATION["indicator_id"],
                    "name": CITY_POPULATION["name"],
                    "status": "unavailable",
                    "dataset_id": CITY_POPULATION["dataset_id"],
                    "source_id": "EUROSTAT",
                    "reason": type(exc).__name__,
                }],
            }
    finally:
        if owns_adapter:
            active_adapter.close()

    if not rows:
        indicators = [{
            "indicator_id": CITY_POPULATION["indicator_id"],
            "name": CITY_POPULATION["name"],
            "status": "unavailable",
            "dataset_id": CITY_POPULATION["dataset_id"],
            "source_id": "EUROSTAT",
            "reason": "no_observation",
        }]
        available_count = 0
    else:
        latest = max(rows, key=lambda row: row["period"])
        indicators = [{
            "indicator_id": CITY_POPULATION["indicator_id"],
            "name": CITY_POPULATION["name"],
            "status": "available",
            "period": latest["period"],
            "value": latest["value"],
            "unit": CITY_POPULATION["unit"],
            "dataset_id": CITY_POPULATION["dataset_id"],
            "source_id": "EUROSTAT",
            "source_updated_at": latest.get("source_updated_at"),
        }]
        available_count = 1

    return {
        "city_code": code,
        "geo_level": "city",
        "source": "Eurostat City Statistics / Urban Audit",
        "minimum_population_scope": 50000,
        "indicator_count": 1,
        "available_count": available_count,
        "complete": available_count == 1,
        "indicators": indicators,
        "notes": [
            "City selection is limited to GISCO Urban Audit cities.",
            "Eurostat Urban Audit city collection covers cities with at least 50,000 inhabitants.",
            "Population uses urb_cpop1 indicator DE1001V (population on 1 January, total).",
        ],
    }
