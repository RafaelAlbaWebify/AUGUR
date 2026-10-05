from __future__ import annotations

from time import monotonic

from app.ingestion.eurostat import EurostatAdapter


CACHE_TTL_SECONDS = 15 * 60
_REGIONAL_CACHE: dict[str, tuple[float, dict]] = {}


REGIONAL_INDICATORS = [
    {
        "indicator_id": "regional_population",
        "name": "Population",
        "dataset_id": "demo_r_pjangrp3",
        "filters": {
            "freq": "A",
            "age": "TOTAL",
            "sex": "T",
            "unit": "NR",
        },
        "unit": "persons",
    },
    {
        "indicator_id": "regional_population_density",
        "name": "Population density",
        "dataset_id": "demo_r_d3dens",
        "filters": {
            "freq": "A",
            "unit": "PER_KM2",
        },
        "unit": "people_per_km2",
    },
    {
        "indicator_id": "regional_gdp_per_capita",
        "name": "GDP per capita",
        "dataset_id": "nama_10r_3gdp",
        "filters": {
            "freq": "A",
            "unit": "EUR_HAB",
            "na_item": "B1GQ",
        },
        "unit": "eur_per_person",
    },
    {
        "indicator_id": "regional_employment_rate",
        "name": "Employment rate, ages 20–64",
        "dataset_id": "lfst_r_lfe2emprt",
        "filters": {
            "freq": "A",
            "age": "Y20-64",
            "sex": "T",
            "unit": "PC",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "regional_unemployment_rate",
        "name": "Unemployment rate, ages 20–64",
        "dataset_id": "lfst_r_lfu3rt",
        "filters": {
            "freq": "A",
            "age": "Y20-64",
            "sex": "T",
            "unit": "PC",
        },
        "unit": "percent",
    },
]


def geographic_level(geo_code: str) -> str:
    code = geo_code.strip().upper()
    if len(code) == 4:
        return "nuts2"
    if len(code) == 5:
        return "nuts3"
    return "unknown"


def _latest_regional_indicator(
    adapter: EurostatAdapter,
    geo_code: str,
    config: dict,
) -> dict:
    filters = {
        "geo": geo_code,
        **config["filters"],
    }

    try:
        payload = adapter.fetch_dataset(config["dataset_id"], filters)
        rows = adapter.normalize(
            geo_code,
            {
                "indicator_id": config["indicator_id"],
                "dataset_id": config["dataset_id"],
                "unit": config["unit"],
            },
            payload,
        )
    except Exception as exc:
        return {
            "indicator_id": config["indicator_id"],
            "name": config["name"],
            "status": "unavailable",
            "dataset_id": config["dataset_id"],
            "source_id": "EUROSTAT",
            "reason": type(exc).__name__,
        }

    if not rows:
        return {
            "indicator_id": config["indicator_id"],
            "name": config["name"],
            "status": "unavailable",
            "dataset_id": config["dataset_id"],
            "source_id": "EUROSTAT",
            "reason": "no_observation",
        }

    latest = max(rows, key=lambda row: row["period"])
    return {
        "indicator_id": config["indicator_id"],
        "name": config["name"],
        "status": "available",
        "period": latest["period"],
        "value": latest["value"],
        "unit": config["unit"],
        "dataset_id": config["dataset_id"],
        "source_id": "EUROSTAT",
        "source_updated_at": latest.get("source_updated_at"),
    }


def regional_evidence(
    geo_code: str,
    adapter: EurostatAdapter | None = None,
) -> dict:
    code = geo_code.strip().upper()

    if adapter is None:
        cached = _REGIONAL_CACHE.get(code)
        if cached and monotonic() - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

    owns_adapter = adapter is None
    active_adapter = adapter or EurostatAdapter(timeout_seconds=20.0, max_retries=2)

    try:
        indicators = [
            _latest_regional_indicator(active_adapter, code, config)
            for config in REGIONAL_INDICATORS
        ]
    finally:
        if owns_adapter:
            active_adapter.close()

    available_count = sum(
        1 for indicator in indicators
        if indicator["status"] == "available"
    )

    result = {
        "geo_code": code,
        "geo_level": geographic_level(code),
        "source": "Eurostat regional statistics",
        "indicator_count": len(indicators),
        "available_count": available_count,
        "complete": available_count == len(indicators),
        "indicators": indicators,
        "notes": [
            "Regional evidence uses the selected Eurostat geographic code directly.",
            "Coverage varies by indicator and region; unavailable series remain explicit.",
            "The geographic code is stable comparison context and can be compared across countries at the same NUTS level.",
        ],
    }

    if adapter is None:
        _REGIONAL_CACHE[code] = (monotonic(), result)

    return result


def regional_comparison(
    geo_codes: list[str],
    adapter: EurostatAdapter | None = None,
) -> dict:
    evidence = [
        regional_evidence(code, adapter=adapter)
        for code in geo_codes
    ]

    indicator_ids = {
        indicator["indicator_id"]
        for item in evidence
        for indicator in item["indicators"]
    }

    rows = []
    for indicator_id in sorted(indicator_ids):
        values = {}
        name = indicator_id
        unit = None
        for item in evidence:
            match = next(
                (
                    indicator
                    for indicator in item["indicators"]
                    if indicator["indicator_id"] == indicator_id
                ),
                None,
            )
            if match:
                name = match["name"]
                unit = match.get("unit") or unit
                values[item["geo_code"]] = match

        rows.append({
            "indicator_id": indicator_id,
            "name": name,
            "unit": unit,
            "regions": values,
        })

    return {
        "regions": [
            {
                "geo_code": item["geo_code"],
                "geo_level": item["geo_level"],
            }
            for item in evidence
        ],
        "indicator_count": len(rows),
        "indicators": rows,
        "notes": [
            "Comparison is descriptive and does not rank regions.",
            "Only like-for-like indicators and geographic levels should be interpreted directly.",
        ],
    }
