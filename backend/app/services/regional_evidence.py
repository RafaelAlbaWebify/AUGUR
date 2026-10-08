from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic

from app.db.analytics import (
    latest_subnational_observations,
    subnational_indicator_series,
    regional_evidence_bundle,
    upsert_subnational_observations,
    latest_regional_sector_employment_for_geo,
    latest_environmental_health_burden_for_geo,
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
    {
        "indicator_id": "regional_household_internet_access",
        "name": "Households with internet access",
        "dataset_id": "isoc_r_iacc_h",
        "filters": {
            "freq": "A",
            "unit": "PC_HH",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "regional_air_passengers_thousands",
        "name": "Air passengers carried",
        "dataset_id": "tran_r_avpa_nm",
        "filters": {
            "freq": "A",
            "tra_meas": "PAS_CRD",
            "unit": "THS_PAS",
        },
        "unit": "thousand_passengers",
    },
]

LOCAL_SUBNATIONAL_INDICATOR_META = {
    "regional_population": {
        "name": "Population",
    },
    "regional_population_density": {
        "name": "Population density",
    },
    "regional_gdp_per_capita": {
        "name": "GDP per capita",
    },
    "regional_employment_rate": {
        "name": "Employment rate",
    },
    "regional_unemployment_rate": {
        "name": "Unemployment rate",
    },
    "regional_international_inmigration_share": {
        "name": "International in-migration",
    },
    "regional_international_outmigration_share": {
        "name": "International out-migration",
    },
    "regional_net_internal_mobility_share": {
        "name": "Net internal mobility",
    },
    "regional_age_adjusted_mortality_per_1000": {
        "name": "Age-adjusted mortality rate",
    },
    "regional_employment_to_population_ratio": {
        "name": "Employment-to-population ratio, ages 15–64",
    },
    "regional_unemployment_rate_oecd": {
        "name": "Unemployment rate, ages 15–64",
    },
    "regional_gdp_per_capita_ppp_usd": {
        "name": "GDP per capita, constant PPP USD",
    },
    "urban_population": {
        "name": "Population",
    },
    "urban_population_density": {
        "name": "Population density",
    },
    "urban_total_dependency_ratio": {
        "name": "Total dependency ratio",
    },
    "urban_youth_dependency_ratio": {
        "name": "Youth dependency ratio",
    },
    "urban_old_age_dependency_ratio": {
        "name": "Old-age dependency ratio",
    },
    "urban_employment_to_population_ratio": {
        "name": "Employment-to-population ratio, ages 15–64",
    },
    "urban_labour_force_participation_rate": {
        "name": "Labour force participation rate, ages 15–64",
    },
    "urban_unemployment_rate": {
        "name": "Unemployment rate, ages 15–64",
    },
}


OECD_TL_EXPECTED_INDICATORS = [
    ("regional_population", "DSD_REG_DEMO@DF_POP_BROAD", "persons"),
    ("regional_population_density", "DSD_REG_DEMO@DF_DENSITY", "people_per_km2"),
    ("regional_international_inmigration_share", "DSD_REG_DEMO@DF_DEMO", "percent"),
    ("regional_international_outmigration_share", "DSD_REG_DEMO@DF_DEMO", "percent"),
    ("regional_net_internal_mobility_share", "DSD_REG_DEMO@DF_DEMO", "percent"),
    ("regional_age_adjusted_mortality_per_1000", "DSD_REG_DEMO@DF_DEMO", "per_1000_people"),
    ("regional_employment_to_population_ratio", "DSD_REG_LAB@DF_RATES", "percent"),
    ("regional_unemployment_rate_oecd", "DSD_REG_LAB@DF_RATES", "percent"),
]

OECD_FUA_EXPECTED_INDICATORS = [
    ("urban_population", "DSD_FUA_DEMO@DF_AGE_SEX", "persons"),
    ("urban_population_density", "DSD_FUA_TERR@DF_DENSITY", "people_per_km2"),
    ("urban_total_dependency_ratio", "DSD_FUA_DEMO@DF_DEPEND", "percent"),
    ("urban_youth_dependency_ratio", "DSD_FUA_DEMO@DF_DEPEND", "percent"),
    ("urban_old_age_dependency_ratio", "DSD_FUA_DEMO@DF_DEPEND", "percent"),
]


def _source_native_expected_configs(
    geography_system: str | None,
) -> list[dict] | None:
    system = str(geography_system or "").upper()
    if system == "OECD_TL_2024":
        definitions = OECD_TL_EXPECTED_INDICATORS
    elif system == "OECD_FUA":
        definitions = OECD_FUA_EXPECTED_INDICATORS
    else:
        return None

    return [
        {
            "indicator_id": indicator_id,
            "name": LOCAL_SUBNATIONAL_INDICATOR_META.get(
                indicator_id,
                {},
            ).get("name", indicator_id.replace("_", " ").title()),
            "dataset_id": dataset_id,
            "unit": unit,
            "source_id": "OECD",
        }
        for indicator_id, dataset_id, unit in definitions
    ]


NUTS3_SAFETY_INDICATORS = [
    {
        "indicator_id": "regional_intentional_homicide_rate",
        "name": "Police-recorded intentional homicide",
        "dataset_id": "crim_gen_reg",
        "filters": {
            "freq": "A",
            "unit": "P_HTHAB",
            "iccs": "ICCS0101",
        },
        "unit": "per_100k_people",
    },
    {
        "indicator_id": "regional_robbery_rate",
        "name": "Police-recorded robbery",
        "dataset_id": "crim_gen_reg",
        "filters": {
            "freq": "A",
            "unit": "P_HTHAB",
            "iccs": "ICCS0401",
        },
        "unit": "per_100k_people",
    },
]



def _indicator_configs_for_geo(code: str) -> list[dict]:
    level = geographic_level(code)
    if level == "nuts2":
        return REGIONAL_INDICATORS
    if level == "nuts3":
        return NUTS3_SAFETY_INDICATORS
    return []


def geographic_level(geo_code: str) -> str:
    code = geo_code.strip().upper()
    if len(code) == 4:
        return "nuts2"
    if len(code) == 5:
        return "nuts3"
    return "unknown"




def _regional_result_from_local(
    code: str,
    rows: list[dict],
    *,
    history_rows: list[dict] | None = None,
    sector_rows: list[dict] | None = None,
    environmental_health_rows: list[dict] | None = None,
) -> dict | None:
    if not rows:
        return None

    local_level = str(rows[0].get("geo_level") or geographic_level(code)).lower()
    local_name = next(
        (
            str(row.get("geo_name"))
            for row in rows
            if row.get("geo_name")
        ),
        None,
    )
    source_ids = sorted({
        str(row["source_id"])
        for row in rows
        if row.get("source_id")
    })

    by_id = {row["indicator_id"]: row for row in rows}
    local_system = str(rows[0].get("geography_system") or "").upper()
    if history_rows is None:
        history_rows = subnational_indicator_series(code, max_points=8)
    history_by_id: dict[str, list[dict]] = {}
    for history_row in history_rows:
        history_by_id.setdefault(history_row["indicator_id"], []).append({
            "period": history_row["period"],
            "value": history_row["value"],
        })

    configured = _indicator_configs_for_geo(code)
    source_native_expected = _source_native_expected_configs(local_system)
    if source_native_expected is not None:
        configured = source_native_expected
    elif local_level not in {"nuts2", "nuts3"}:
        configured = [
            {
                "indicator_id": indicator_id,
                "name": LOCAL_SUBNATIONAL_INDICATOR_META.get(
                    indicator_id,
                    {},
                ).get("name", indicator_id.replace("_", " ").title()),
                "dataset_id": row["dataset_id"],
                "unit": row.get("unit"),
                "source_id": row.get("source_id"),
            }
            for indicator_id, row in sorted(by_id.items())
        ]

    indicators = []
    for config in configured:
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
                "history": history_by_id.get(config["indicator_id"], []),
            })
        elif local_level in {"nuts2", "nuts3"} or source_native_expected is not None:
            indicators.append({
                "indicator_id": config["indicator_id"],
                "name": config["name"],
                "status": "unavailable",
                "dataset_id": config["dataset_id"],
                "source_id": config.get("source_id", "EUROSTAT"),
                "reason": "not_cached",
                "unit": config.get("unit"),
                "history": [],
            })

    available_count = sum(
        1
        for item in indicators
        if item["status"] == "available"
    )
    source_label = (
        "OECD urban statistics"
        if source_ids == ["OECD"] and local_level in {"city", "fua"}
        else "OECD regional statistics"
        if source_ids == ["OECD"]
        else "Eurostat regional statistics"
        if source_ids == ["EUROSTAT"]
        else "local subnational evidence"
    )

    sector_context = (
        _regional_sector_context(code, sector_rows)
        if local_level == "nuts2"
        else {
            "status": "unavailable",
            "reason": "sector_context_not_available_for_geography_system",
            "dataset_id": None,
            "source_id": None,
            "sectors": [],
        }
    )
    environmental_context = (
        _environmental_health_context(code, environmental_health_rows)
        if local_level in {"nuts2", "nuts3"}
        else {
            "status": "unavailable",
            "reason": "environmental_health_not_available_for_geography_system",
            "source_id": None,
            "dataset_id": None,
            "metrics": [],
        }
    )

    return {
        "geography_system": (
            rows[0].get("geography_system")
            if rows
            else None
        ),
        "geo_code": code,
        "geo_name": local_name,
        "geo_level": local_level,
        "source": f"AUGUR local store · {source_label}",
        "source_ids": source_ids,
        "storage": "duckdb",
        "indicator_count": len(indicators),
        "available_count": available_count,
        "complete": available_count == len(indicators),
        "indicators": indicators,
        "sector_structure": sector_context,
        "environmental_health": environmental_context,
        "notes": (
            [
                "Regional evidence is served from AUGUR's local analytical store when available.",
                "Coverage varies by indicator and region; unavailable series remain explicit.",
                "NUTS geographic levels retain Eurostat-specific comparison semantics.",
            ]
            if local_level in {"nuts2", "nuts3"}
            else (
                [
                    "Urban evidence is served from AUGUR's local analytical store.",
                    "OECD city and Functional Urban Area definitions remain distinct geographic levels.",
                    "Only metrics explicitly published for this OECD urban geography are shown.",
                    "No Urban Audit metrics are inferred for OECD urban geographies.",
                ]
                if local_level in {"city", "fua"}
                else [
                    "Subnational evidence is served from AUGUR's local analytical store.",
                    "Only metrics explicitly published for this source-native geography are shown.",
                    "OECD TL2/TL3 levels are not treated as interchangeable with Eurostat NUTS levels.",
                    "No missing Eurostat metrics are inferred for OECD territorial levels.",
                ]
            )
        ),
    }



def _environmental_health_context(
    code: str,
    rows: list[dict] | None = None,
) -> dict:
    if rows is None:
        rows = latest_environmental_health_burden_for_geo(code)
    if not rows:
        return {
            "status": "unavailable",
            "reason": "not_cached",
            "source_id": "EEA",
            "dataset_id": "EEA_PM25_PREMATURE_DEATHS_NUTS23",
            "comparison_policy": {
                "safe_for_direct_cross_region_comparison": False,
                "reason": "published_as_absolute_counts",
                "preferred_comparison_basis": "population_normalized_rate_if_officially_available",
            },
            "metrics": [],
        }

    metrics = [
        {
            "burden_type": row["burden_type"],
            "label": row.get("burden_label") or row["burden_type"],
            "period": row["period"],
            "value": row["value"],
            "unit_code": row["unit_code"],
            "unit_label": row.get("unit_label") or row["unit_code"],
            "obs_status": row.get("obs_status"),
        }
        for row in rows
    ]
    return {
        "status": "available",
        "source_id": rows[0]["source_id"],
        "dataset_id": rows[0]["dataset_id"],
        "dataset_version": rows[0]["dataset_version"],
        "geo_level": rows[0]["geo_level"],
        "period": max(row["period"] for row in rows),
        "comparison_policy": {
            "safe_for_direct_cross_region_comparison": False,
            "reason": "published_as_absolute_counts",
            "preferred_comparison_basis": "population_normalized_rate_if_officially_available",
        },
        "metrics": metrics,
        "notes": [
            "EEA PM2.5 health burden is attributable-impact evidence, not a measurement of current ambient concentration.",
            "Published NUTS granularity, units and observation status are preserved.",
            "Published PMD/YLL values are absolute counts; AUGUR does not use them to rank regions of different population sizes.",
            "Premature deaths and years of life lost remain separate measures and are not combined into an AUGUR score.",
        ],
    }


def _regional_sector_context(
    code: str,
    rows: list[dict] | None = None,
) -> dict:
    if geographic_level(code) != "nuts2":
        return {
            "status": "unavailable",
            "reason": "sector_context_requires_nuts2",
            "dataset_id": "lfst_r_lfe2en2",
            "source_id": "EUROSTAT",
            "sectors": [],
        }

    if rows is None:
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
        "history": [
            {
                "period": row["period"],
                "value": row["value"],
            }
            for row in sorted(rows, key=lambda row: row["period"])[-8:]
        ],
    }


def regional_evidence(
    geo_code: str,
    adapter: EurostatAdapter | None = None,
    force_refresh: bool = False,
    geography_system: str | None = None,
) -> dict:
    code = geo_code.strip().upper()
    system = geography_system.upper() if geography_system else None
    cache_key = f"{system or '*'}:{code}"

    if adapter is None and not force_refresh:
        cached = _REGIONAL_CACHE.get(cache_key)
        if cached and monotonic() - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

        bundle = regional_evidence_bundle(
            code,
            max_history_points=8,
            geography_system=system,
        )
        local_rows = bundle["latest"]
        local = _regional_result_from_local(
            code,
            local_rows,
            history_rows=bundle["history"],
            sector_rows=bundle["sectors"],
            environmental_health_rows=bundle["environmental_health"],
        )
        if local:
            _REGIONAL_CACHE[cache_key] = (monotonic(), local)
            return local

        # Interactive reads must never block on Eurostat. Missing local
        # evidence is repaired by refresh/sync flows or an explicit
        # force_refresh, not while the user is selecting a region.
        indicators = [
            {
                "indicator_id": config["indicator_id"],
                "name": config["name"],
                "status": "unavailable",
                "dataset_id": config["dataset_id"],
                "source_id": "EUROSTAT",
                "reason": "not_cached",
                "history": [],
            }
            for config in _indicator_configs_for_geo(code)
        ]
        result = {
            "geography_system": system,
            "geo_code": code,
            "geo_level": (
                geographic_level(code)
                if system in {None, "NUTS_2024"}
                else "unknown"
            ),
            "source": "AUGUR local store · Eurostat regional statistics",
            "storage": "duckdb",
            "indicator_count": len(indicators),
            "available_count": 0,
            "complete": False,
            "indicators": indicators,
            "sector_structure": _regional_sector_context(code, bundle["sectors"]),
            "environmental_health": _environmental_health_context(code, bundle["environmental_health"]),
            "notes": [
                "Interactive regional reads are local-only and never wait for an external provider.",
                "Missing evidence is refreshed through AUGUR sync/repair flows.",
                "Coverage varies by indicator and region; unavailable series remain explicit.",
            ],
        }
        _REGIONAL_CACHE[cache_key] = (monotonic(), result)
        return result

    owns_adapter = adapter is None
    active_adapter = adapter or EurostatAdapter(timeout_seconds=20.0, max_retries=2)

    try:
        indicators = [
            _latest_regional_indicator(active_adapter, code, config)
            for config in _indicator_configs_for_geo(code)
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
        "sector_structure": _regional_sector_context(code),
        "environmental_health": _environmental_health_context(code),
        "notes": [
            "Regional evidence uses the selected Eurostat geographic code directly.",
            "Coverage varies by indicator and region; unavailable series remain explicit.",
            "The geographic code is stable comparison context and can be compared across countries at the same NUTS level.",
            "NUTS2 access indicators are descriptive connectivity context, not quality-of-life scores.",
            "NUTS3 police-recorded crime is descriptive safety context and can be affected by legal, reporting and recording differences.",
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
        _REGIONAL_CACHE[cache_key] = (monotonic(), result)

    return result


def sync_regional_evidence_codes(
    geo_codes: list[str],
    adapter: EurostatAdapter | None = None,
) -> dict:
    codes = sorted({
        str(code).strip().upper()
        for code in geo_codes
        if str(code).strip()
    })

    owns_adapter = adapter is None
    active_adapter = adapter or EurostatAdapter(
        timeout_seconds=90.0,
        max_retries=3,
    )

    rows_to_store = []
    results = []

    try:
        for code in codes:
            indicators = [
                _latest_regional_indicator(
                    active_adapter,
                    code,
                    config,
                )
                for config in _indicator_configs_for_geo(code)
            ]
            available_count = sum(
                1
                for item in indicators
                if item["status"] == "available"
            )
            results.append({
                "geo_code": code,
                "geo_level": geographic_level(code),
                "indicator_count": len(indicators),
                "available_count": available_count,
            })

            rows_to_store.extend([
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
            ])
    finally:
        if owns_adapter:
            active_adapter.close()

    stored = upsert_subnational_observations(rows_to_store)
    for code in codes:
        _REGIONAL_CACHE.pop(code, None)

    return {
        "geo_code_count": len(codes),
        "geographies_with_data": sum(
            1 for item in results
            if item["available_count"] > 0
        ),
        "rows_upserted": stored,
        "results": results,
    }


def regional_comparison(
    geo_codes: list[str],
    adapter: EurostatAdapter | None = None,
    geography_system: str | None = None,
) -> dict:
    evidence = [
        regional_evidence(
            code,
            adapter=adapter,
            geography_system=geography_system,
        )
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
                "geo_name": item.get("geo_name"),
                "geo_level": item["geo_level"],
                "source": item.get("source"),
                "source_ids": item.get("source_ids", []),
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
            "Only like-for-like indicators from the same geography system and geographic level should be interpreted directly.",
            "Sector comparison describes employment composition, not vacancy demand or hiring probability.",
        ],
    }
