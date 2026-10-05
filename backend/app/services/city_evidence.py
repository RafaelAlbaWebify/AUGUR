from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic

from app.db.analytics import latest_subnational_observations, upsert_subnational_observations
from app.ingestion.eurostat import EurostatAdapter


CACHE_TTL_SECONDS = 15 * 60
_CITY_CACHE: dict[str, tuple[float, dict]] = {}


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




def _city_result_from_local(code: str, rows: list[dict]) -> dict | None:
    match = next((row for row in rows if row["indicator_id"] == CITY_POPULATION["indicator_id"]), None)
    if not match:
        return None

    return {
        "city_code": code,
        "geo_level": "city",
        "source": "AUGUR local store · Eurostat City Statistics / Urban Audit",
        "storage": "duckdb",
        "minimum_population_scope": 50000,
        "indicator_count": 1,
        "available_count": 1,
        "complete": True,
        "indicators": [{
            "indicator_id": CITY_POPULATION["indicator_id"],
            "name": CITY_POPULATION["name"],
            "status": "available",
            "period": match["period"],
            "value": match["value"],
            "unit": match["unit"],
            "dataset_id": match["dataset_id"],
            "source_id": match["source_id"],
            "source_updated_at": match.get("source_updated_at"),
        }],
        "notes": [
            "City evidence is served from AUGUR's local analytical store when available.",
            "Eurostat Urban Audit city collection covers cities with at least 50,000 inhabitants.",
        ],
    }

def city_evidence(
    city_code: str,
    adapter: EurostatAdapter | None = None,
    force_refresh: bool = False,
) -> dict:
    code = city_code.strip().upper()

    if adapter is None and not force_refresh:
        local = _city_result_from_local(code, latest_subnational_observations(code))
        if local:
            return local

        cached = _CITY_CACHE.get(code)
        if cached and monotonic() - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

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
            result = {
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
            if adapter is None:
                _CITY_CACHE[code] = (monotonic(), result)
            return result
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

    result = {
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

    if adapter is None:
        rows_to_store = [
            {
                "geo_code": code,
                "geo_level": "city",
                "indicator_id": item["indicator_id"],
                "period": item["period"],
                "value": item["value"],
                "unit": item.get("unit"),
                "source_id": item["source_id"],
                "dataset_id": item["dataset_id"],
                "retrieved_at": datetime.now(timezone.utc),
                "source_updated_at": item.get("source_updated_at"),
            }
            for item in indicators
            if item["status"] == "available"
        ]
        upsert_subnational_observations(rows_to_store)
        _CITY_CACHE[code] = (monotonic(), result)

    return result
