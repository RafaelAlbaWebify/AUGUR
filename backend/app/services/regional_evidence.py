from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic

from app.db.analytics import (
    latest_subnational_observations,
    upsert_subnational_observations,
    latest_regional_sector_employment_for_geo,
)
from app.ingestion.eurostat import EurostatAdapter


CACHE_TTL_SECONDS = 15 * 60
_REGIONAL_CACHE: dict[str, tuple[float, dict]] = {}


REGIONAL_INDICATORS = [
    {
        "indicator_id": "regional_unmet_medical_needs",
        "name": "Unmet medical examination needs",
        "dataset_id": "hlth_silc_08_r",
        "filters": {
            "freq": "A",
            "reason": "TXP_TFAR_WLIST",
            "unit": "PC",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "regional_hospital_beds_per_100k",
        "name": "Available hospital beds",
        "dataset_id": "hlth_rs_bdsrg2",
        "filters": {
            "freq": "A",
            "unit": "P_HTHAB",
        },
        "unit": "per_100k_people",
    },
    {
        "indicator_id": "regional_disposable_income_pps_per_capita",
        "name": "Disposable household income per inhabitant (PPS)",
        "dataset_id": "nama_10r_2hhinc",
        "filters": {
            "freq": "A",
            "unit": "PPS_EU27_2020_HAB",
            "direct": "BAL",
            "na_item": "B6N",
        },
        "unit": "pps_per_person",
    },
    {
        "indicator_id": "regional_housing_cost_overburden_rate",
        "name": "Housing cost overburden rate",
        "dataset_id": "ilc_lvho07_r",
        "filters": {
            "freq": "A",
            "unit": "PC",
        },
        "unit": "percent",
    },
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




def _regional_result_from_local(code: str, rows: list[dict]) -> dict | None:
    if not rows:
        return None

    by_id = {row["indicator_id"]: row for row in rows}
    indicators = []
    for config in REGIONAL_INDICATORS:
        row = by_id.get(config["indicator_id"])
        if row:
            indicators.append({
                "indicator_id": config["indicator_id"],
                "name": config["name"],
                "status": "available",
                "period": row["period"],
                "value": row["value"],
                "unit": row["unit"],
                "dataset_id": row["dataset_id"],
                "source_id": row["source_id"],
                "source_updated_at": row.get("source_updated_at"),
            })
        else:
            indicators.append({
                "indicator_id": config["indicator_id"],
                "name": config["name"],
                "status": "unavailable",
                "dataset_id": config["dataset_id"],
                "source_id": "EUROSTAT",
                "reason": "not_cached",
            })

    available_count = sum(1 for item in indicators if item["status"] == "available")
    return {
        "geo_code": code,
        "geo_level": geographic_level(code),
        "source": "AUGUR local store · Eurostat regional statistics",
        "storage": "duckdb",
        "indicator_count": len(indicators),
        "available_count": available_count,
        "complete": available_count == len(indicators),
        "indicators": indicators,
        "sector_structure": _regional_sector_context(code),
        "notes": [
            "Regional evidence is served from AUGUR's local analytical store when available.",
            "Coverage varies by indicator and region; unavailable series remain explicit.",
            "The geographic code is stable comparison context and can be compared across countries at the same NUTS level.",
        ],
    }



def _regional_sector_context(code: str) -> dict:
    if geographic_level(code) != "nuts2":
        return {
            "status": "unavailable",
            "reason": "sector_context_requires_nuts2",
            "dataset_id": "lfst_r_lfe2en2",
            "source_id": "EUROSTAT",
            "sectors": [],
        }

    rows = latest_regional_sector_employment_for_geo(code)
    if not rows:
        return {
            "status": "unavailable",
            "reason": "not_cached",
            "dataset_id": "lfst_r_lfe2en2",
            "source_id": "EUROSTAT",
            "sectors": [],
        }

    total_row = next(
        (row for row in rows if row["nace_code"] == "TOTAL"),
        None,
    )
    total = (
        float(total_row["employment_thousands"])
        if total_row and total_row.get("employment_thousands") is not None
        else None
    )

    sector_rows = [
        row for row in rows
        if row["nace_code"] != "TOTAL"
        and row.get("employment_thousands") is not None
    ]
    sectors = []
    for row in sector_rows:
        value = float(row["employment_thousands"])
        sectors.append({
            "nace_code": row["nace_code"],
            "nace_label": row.get("nace_label"),
            "period": row["period"],
            "employment_thousands": value,
            "employment_share_pct": (
                round((value / total) * 100.0, 2)
                if total and total > 0
                else None
            ),
        })

    return {
        "status": "available",
        "dataset_id": rows[0]["dataset_id"],
        "source_id": rows[0]["source_id"],
        "period": max(row["period"] for row in rows),
        "total_employment_thousands": total,
        "sector_count": len(sectors),
        "top_sectors": sorted(
            sectors,
            key=lambda item: item["employment_thousands"],
            reverse=True,
        )[:8],
        "notes": [
            "Sector structure describes employment composition, not vacancies.",
            "Employment shares use the published regional total as denominator when available.",
        ],
    }

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
    force_refresh: bool = False,
) -> dict:
    code = geo_code.strip().upper()

    if adapter is None and not force_refresh:
        local = _regional_result_from_local(code, latest_subnational_observations(code))
        if local:
            return local

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
        rows_to_store = [
            {
                "geo_code": code,
                "geo_level": geographic_level(code),
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

    sector_codes = sorted({
        sector["nace_code"]
        for item in evidence
        for sector in (
            item.get("sector_structure", {}).get("top_sectors", [])
            if item.get("sector_structure", {}).get("status") == "available"
            else []
        )
    })
    sector_rows = []
    for nace_code in sector_codes:
        regions = {}
        label = nace_code
        for item in evidence:
            sector = next(
                (
                    candidate
                    for candidate in item.get("sector_structure", {}).get("top_sectors", [])
                    if candidate["nace_code"] == nace_code
                ),
                None,
            )
            if sector:
                label = sector.get("nace_label") or label
                regions[item["geo_code"]] = sector
        sector_rows.append({
            "nace_code": nace_code,
            "nace_label": label,
            "regions": regions,
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
        "sector_comparison": {
            "status": "available" if sector_rows else "unavailable",
            "dataset_id": "lfst_r_lfe2en2",
            "source_id": "EUROSTAT",
            "sectors": sector_rows,
            "role": "regional_employment_structure_only",
        },
        "notes": [
            "Comparison is descriptive and does not rank regions.",
            "Only like-for-like indicators and geographic levels should be interpreted directly.",
            "Sector comparison describes employment composition, not vacancy demand or hiring probability.",
        ],
    }
