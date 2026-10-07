from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic

from app.db.analytics import (
    latest_subnational_observations,
    subnational_indicator_series,
    city_evidence_bundle,
    upsert_subnational_observations,
)
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eea_city_air import fetch_city_pm25_annual
from app.services.eea_city_catalog import resolve_eea_city


CACHE_TTL_SECONDS = 15 * 60
_CITY_CACHE: dict[str, tuple[float, dict]] = {}
AIR_QUALITY_VERIFIED_YEAR = 2024


CITY_INDICATORS = [
    {
        "indicator_id": "city_population",
        "name": "Population",
        "dataset_id": "urb_cpop1",
        "indic_ur": "DE1001V",
        "unit": "persons",
        "category": "demography",
    },
    {
        "indicator_id": "city_median_age",
        "name": "Median population age",
        "dataset_id": "urb_cpopstr",
        "indic_ur": "DE1073V",
        "unit": "years",
        "category": "demography",
    },
    {
        "indicator_id": "city_public_transport_commute_share",
        "name": "Journeys to work by public transport",
        "dataset_id": "urb_ctran",
        "indic_ur": "TT1010V",
        "unit": "percent",
        "category": "mobility",
    },
    {
        "indicator_id": "city_walk_commute_share",
        "name": "Journeys to work by foot",
        "dataset_id": "urb_ctran",
        "indic_ur": "TT1008V",
        "unit": "percent",
        "category": "mobility",
    },
    {
        "indicator_id": "city_registered_cars_per_1000",
        "name": "Registered cars",
        "dataset_id": "urb_ctran",
        "indic_ur": "TT1057I",
        "unit": "per_1000_people",
        "category": "mobility",
    },
    {
        "indicator_id": "city_monthly_transit_pass",
        "name": "Monthly public transport ticket",
        "dataset_id": "urb_ctran",
        "indic_ur": "TT1080V",
        "unit": "eur_monthly",
        "category": "mobility",
    },
    {
        "indicator_id": "city_tourist_nights_per_resident",
        "name": "Tourist overnight stays per resident",
        "dataset_id": "urb_ctour",
        "indic_ur": "CR2011I",
        "unit": "nights_per_person",
        "category": "tourism",
    },
    {
        "indicator_id": "city_tourist_beds_per_1000",
        "name": "Tourist bed-places",
        "dataset_id": "urb_ctour",
        "indic_ur": "CR2010I",
        "unit": "per_1000_people",
        "category": "tourism",
    },
]

CITY_POPULATION = CITY_INDICATORS[0]




def _city_result_from_local(
    code: str,
    rows: list[dict],
    *,
    history_rows: list[dict] | None = None,
) -> dict | None:
    by_id = {
        row["indicator_id"]: row
        for row in rows
    }
    if history_rows is None:
        history_rows = subnational_indicator_series(code, max_points=8)
    history_by_id: dict[str, list[dict]] = {}
    for history_row in history_rows:
        history_by_id.setdefault(history_row["indicator_id"], []).append({
            "period": history_row["period"],
            "value": history_row["value"],
        })

    if not any(
        config["indicator_id"] in by_id
        for config in CITY_INDICATORS
    ) and "city_pm25_annual_mean_observed" not in by_id:
        return None

    indicators = []
    for config in CITY_INDICATORS:
        row = by_id.get(config["indicator_id"])
        if row:
            indicators.append({
                "indicator_id": config["indicator_id"],
                "name": config["name"],
                "category": config["category"],
                "status": "available",
                "period": row["period"],
                "value": row["value"],
                "unit": row["unit"],
                "dataset_id": row["dataset_id"],
                "source_id": row["source_id"],
                "source_updated_at": row.get("source_updated_at"),
                "history": history_by_id.get(config["indicator_id"], []),
            })
        else:
            indicators.append({
                "indicator_id": config["indicator_id"],
                "name": config["name"],
                "category": config["category"],
                "status": "unavailable",
                "dataset_id": config["dataset_id"],
                "source_id": "EUROSTAT",
                "reason": "not_cached",
                "history": [],
            })

    pm25 = by_id.get("city_pm25_annual_mean_observed")
    if pm25:
        indicators.append({
            "indicator_id": "city_pm25_annual_mean_observed",
            "name": "Observed annual mean PM2.5",
            "category": "environment",
            "status": "available",
            "period": pm25["period"],
            "value": pm25["value"],
            "unit": pm25["unit"],
            "dataset_id": pm25["dataset_id"],
            "source_id": pm25["source_id"],
            "source_updated_at": pm25.get("source_updated_at"),
            "history": history_by_id.get("city_pm25_annual_mean_observed", []),
        })
    else:
        indicators.append({
            "indicator_id": "city_pm25_annual_mean_observed",
            "name": "Observed annual mean PM2.5",
            "category": "environment",
            "status": "unavailable",
            "dataset_id": "EEA_AIR_QUALITY_E1A_CITY_MEASUREMENTS",
            "source_id": "EEA",
            "reason": "not_cached",
            "history": [],
        })

    available_count = sum(
        1 for item in indicators
        if item["status"] == "available"
    )

    return {
        "city_code": code,
        "geo_level": "city",
        "source": "AUGUR local store · Eurostat Urban Audit + EEA air quality",
        "storage": "duckdb",
        "minimum_population_scope": 50000,
        "indicator_count": len(indicators),
        "available_count": available_count,
        "complete": available_count == len(indicators),
        "indicators": indicators,
        "notes": [
            "City evidence is served from AUGUR's local analytical store when available.",
            "Urban Audit coverage varies by city and indicator; missing observations remain explicit.",
            "Transport and tourism indicators preserve Eurostat Urban Audit definitions and publication years.",
            "Observed PM2.5 uses validated EEA E1a monitoring data and is not a population-exposure model.",
        ],
    }


def _fetch_city_indicators(
    adapter: EurostatAdapter,
    code: str,
) -> list[dict]:
    by_dataset: dict[str, list[dict]] = {}
    for config in CITY_INDICATORS:
        by_dataset.setdefault(config["dataset_id"], []).append(config)

    indicators: list[dict] = []
    for dataset_id, configs in by_dataset.items():
        try:
            payload = adapter.fetch_dataset(
                dataset_id,
                {
                    "cities": code,
                    "freq": "A",
                },
            )
        except Exception as exc:
            indicators.extend([
                {
                    "indicator_id": config["indicator_id"],
                    "name": config["name"],
                    "category": config["category"],
                    "status": "unavailable",
                    "dataset_id": dataset_id,
                    "source_id": "EUROSTAT",
                    "reason": type(exc).__name__,
                    "history": [],
                }
                for config in configs
            ])
            continue

        for config in configs:
            rows = adapter.normalize(
                code,
                {
                    "indicator_id": config["indicator_id"],
                    "dataset_id": dataset_id,
                    "unit": config["unit"],
                    "dimension_values": {
                        "indic_ur": config["indic_ur"],
                    },
                },
                payload,
            )
            if not rows:
                indicators.append({
                    "indicator_id": config["indicator_id"],
                    "name": config["name"],
                    "status": "unavailable",
                    "dataset_id": dataset_id,
                    "source_id": "EUROSTAT",
                    "reason": "no_observation",
                    "history": [],
                })
                continue

            ordered = sorted(rows, key=lambda row: row["period"])
            latest = ordered[-1]
            indicators.append({
                "indicator_id": config["indicator_id"],
                "name": config["name"],
                "category": config["category"],
                "status": "available",
                "period": latest["period"],
                "value": latest["value"],
                "unit": config["unit"],
                "dataset_id": dataset_id,
                "source_id": "EUROSTAT",
                "source_updated_at": latest.get("source_updated_at"),
                "history": [
                    {
                        "period": row["period"],
                        "value": row["value"],
                    }
                    for row in ordered[-8:]
                ],
            })

    return indicators


def sync_city_evidence_codes(
    city_codes: list[str],
    adapter: EurostatAdapter | None = None,
    *,
    refresh_pm25: bool = True,
) -> dict:
    codes = sorted({
        str(code).strip().upper()
        for code in city_codes
        if str(code).strip()
    })
    if not codes:
        return {
            "city_code_count": 0,
            "cities_with_data": 0,
            "rows_upserted": 0,
            "pm25_refreshed": 0,
            "results": [],
        }

    owns_adapter = adapter is None
    active_adapter = adapter or EurostatAdapter(
        timeout_seconds=90.0,
        max_retries=3,
    )

    by_dataset: dict[str, list[dict]] = {}
    for config in CITY_INDICATORS:
        by_dataset.setdefault(config["dataset_id"], []).append(config)

    rows_to_store: list[dict] = []
    availability: dict[str, set[str]] = {code: set() for code in codes}
    failures: list[dict] = []

    try:
        for dataset_id, configs in by_dataset.items():
            try:
                payload = active_adapter.fetch_dataset(
                    dataset_id,
                    {
                        "cities": codes,
                        "freq": "A",
                    },
                )
            except Exception as exc:
                failures.append({
                    "dataset_id": dataset_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                })
                continue

            for code in codes:
                for config in configs:
                    normalized = active_adapter.normalize(
                        code,
                        {
                            "indicator_id": config["indicator_id"],
                            "dataset_id": dataset_id,
                            "unit": config["unit"],
                            "dimension_values": {
                                "cities": code,
                                "indic_ur": config["indic_ur"],
                            },
                        },
                        payload,
                    )
                    if normalized:
                        availability[code].add(config["indicator_id"])

                    rows_to_store.extend([
                        {
                            "geo_code": code,
                            "geo_level": "city",
                            "indicator_id": config["indicator_id"],
                            "period": row["period"],
                            "value": row["value"],
                            "unit": config["unit"],
                            "source_id": row["source_id"],
                            "dataset_id": dataset_id,
                            "retrieved_at": row["retrieved_at"],
                            "source_updated_at": row.get("source_updated_at"),
                        }
                        for row in normalized
                    ])
    finally:
        if owns_adapter:
            active_adapter.close()

    rows_upserted = upsert_subnational_observations(rows_to_store)

    pm25_refreshed = 0
    if refresh_pm25:
        for code in codes:
            if _refresh_city_pm25(code):
                pm25_refreshed += 1

    for code in codes:
        _CITY_CACHE.pop(code, None)

    results = [
        {
            "city_code": code,
            "available_indicator_count": len(availability[code]),
            "available_indicator_ids": sorted(availability[code]),
        }
        for code in codes
    ]

    return {
        "city_code_count": len(codes),
        "cities_with_data": sum(
            1 for code in codes
            if availability[code]
        ),
        "rows_upserted": rows_upserted,
        "pm25_refreshed": pm25_refreshed,
        "dataset_failures": failures,
        "results": results,
    }


def _refresh_city_pm25(code: str) -> bool:
    try:
        resolved = resolve_eea_city(code)
        if resolved is None:
            return False

        result = fetch_city_pm25_annual(
            resolved["eea_city_name"],
            resolved["country_code"],
            AIR_QUALITY_VERIFIED_YEAR,
        )
        if result.get("status") != "available":
            return False

        upsert_subnational_observations([
            {
                "geo_code": code,
                "geo_name": resolved.get("gisco_city_name"),
                "geo_level": "city",
                "indicator_id": "city_pm25_annual_mean_observed",
                "period": result["year"],
                "value": result["value"],
                "unit": result["unit"],
                "source_id": result["source_id"],
                "dataset_id": result["dataset_id"],
                "retrieved_at": datetime.now(timezone.utc),
                "source_updated_at": None,
            }
        ])
        return True
    except Exception:
        return False

def city_evidence(
    city_code: str,
    adapter: EurostatAdapter | None = None,
    force_refresh: bool = False,
) -> dict:
    code = city_code.strip().upper()

    if adapter is None and not force_refresh:
        cached = _CITY_CACHE.get(code)
        if cached and monotonic() - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

        bundle = city_evidence_bundle(code, max_history_points=8)
        local_rows = bundle["latest"]
        local = _city_result_from_local(
            code,
            local_rows,
            history_rows=bundle["history"],
        )
        if local:
            _CITY_CACHE[code] = (monotonic(), local)
            return local

        # Interactive city reads are local-only. Population and EEA PM2.5
        # are populated by sync/repair flows or explicit force_refresh.
        result = {
            "city_code": code,
            "geo_level": "city",
            "source": "AUGUR local store · Eurostat Urban Audit + EEA air quality",
            "storage": "duckdb",
            "minimum_population_scope": 50000,
            "indicator_count": len(CITY_INDICATORS) + 1,
            "available_count": 0,
            "complete": False,
            "indicators": [
                *[
                    {
                        "indicator_id": config["indicator_id"],
                        "name": config["name"],
                        "status": "unavailable",
                        "dataset_id": config["dataset_id"],
                        "source_id": "EUROSTAT",
                        "reason": "not_cached",
                        "history": [],
                    }
                    for config in CITY_INDICATORS
                ],
                {
                    "indicator_id": "city_pm25_annual_mean_observed",
                    "name": "Observed annual mean PM2.5",
                    "category": "environment",
                    "status": "unavailable",
                    "dataset_id": "EEA_AIR_QUALITY_E1A_CITY_MEASUREMENTS",
                    "source_id": "EEA",
                    "reason": "not_cached",
                    "history": [],
                },
            ],
            "notes": [
                "Interactive city reads are local-only and never wait for external providers.",
                "Missing city evidence is refreshed through AUGUR sync/repair flows.",
            ],
        }
        _CITY_CACHE[code] = (monotonic(), result)
        return result

    owns_adapter = adapter is None
    active_adapter = adapter or EurostatAdapter(timeout_seconds=20.0, max_retries=2)

    try:
        indicators = _fetch_city_indicators(active_adapter, code)
    finally:
        if owns_adapter:
            active_adapter.close()

    available_count = sum(
        1 for item in indicators
        if item["status"] == "available"
    )

    result = {
        "city_code": code,
        "geo_level": "city",
        "source": "Eurostat City Statistics / Urban Audit",
        "minimum_population_scope": 50000,
        "indicator_count": len(indicators),
        "available_count": available_count,
        "complete": available_count == len(indicators),
        "indicators": indicators,
        "notes": [
            "City selection is limited to GISCO Urban Audit cities.",
            "Eurostat Urban Audit city collection covers cities with at least 50,000 inhabitants.",
            "Urban Audit indicators are fetched by stable INDIC_UR codes and remain explicit when a city has no observation.",
            "Population uses urb_cpop1 indicator DE1001V (population on 1 January, total).",
            "Transport uses urb_ctran; tourism uses urb_ctour; population structure uses urb_cpopstr.",
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
        if force_refresh:
            _refresh_city_pm25(code)

        bundle = city_evidence_bundle(code, max_history_points=8)
        combined = _city_result_from_local(
            code,
            bundle["latest"],
            history_rows=bundle["history"],
        )
        if combined:
            _CITY_CACHE[code] = (monotonic(), combined)
            return combined

        _CITY_CACHE[code] = (monotonic(), result)

    return result
