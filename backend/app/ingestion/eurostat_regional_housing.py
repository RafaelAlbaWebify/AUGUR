from __future__ import annotations

from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_labour import normalize_subnational


REGIONAL_HOUSING_SERIES = [
    {
        "indicator_id": "regional_disposable_income_pps_per_capita",
        "dataset_id": "nama_10r_2hhinc",
        "filters": {
            "freq": "A",
            "unit": "PPS_EU27_2020_HAB",
            "direct": "BAL",
            "na_item": "B6N",
            "geoLevel": "nuts2",
        },
        "unit": "pps_per_person",
    },
    {
        "indicator_id": "regional_housing_cost_overburden_rate",
        "dataset_id": "ilc_lvho07_r",
        "filters": {
            "freq": "A",
            "unit": "PC",
            "geoLevel": "nuts2",
        },
        "unit": "percent",
    },
]

DATASETS = [
    {
        "id": "nama_10r_2hhinc",
        "role": "regional_disposable_income",
        "filters": {
            "freq": "A",
            "geoLevel": "nuts2",
            "time": "2024",
        },
    },
    {
        "id": "ilc_lvho07_r",
        "role": "regional_housing_cost_overburden",
        "filters": {
            "freq": "A",
            "geoLevel": "nuts2",
            "time": "2025",
        },
    },
]


def _ordered_codes(dimension: dict) -> list[str]:
    index = dimension.get("category", {}).get("index", {})
    if isinstance(index, list):
        return list(index)
    if isinstance(index, dict):
        return [
            code
            for code, _position in sorted(
                index.items(),
                key=lambda item: item[1],
            )
        ]
    return []


def inspect_regional_housing_sources(
    adapter: EurostatAdapter,
) -> dict:
    results = []

    for config in DATASETS:
        try:
            payload = adapter.fetch_dataset(
                config["id"],
                config["filters"],
            )
        except Exception as exc:
            results.append({
                "dataset_id": config["id"],
                "role": config["role"],
                "status": "unavailable",
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue

        dimensions = payload.get("dimension", {})
        dimension_ids = payload.get("id", [])
        dimension_summary = {}

        for dimension_id in dimension_ids:
            dimension = dimensions.get(dimension_id, {})
            codes = _ordered_codes(dimension)
            labels = dimension.get("category", {}).get("label", {})
            dimension_summary[dimension_id] = {
                "label": dimension.get("label"),
                "code_count": len(codes),
                "sample_codes": codes[:30],
                "sample_labels": {
                    code: labels.get(code)
                    for code in codes[:30]
                },
            }

        geo_codes = _ordered_codes(dimensions.get("geo", {}))
        target_regions = {
            "ES": [code for code in geo_codes if code.startswith("ES") and len(code) == 4],
            "PT": [code for code in geo_codes if code.startswith("PT") and len(code) == 4],
            "IE": [code for code in geo_codes if code.startswith("IE") and len(code) == 4],
        }

        results.append({
            "dataset_id": config["id"],
            "role": config["role"],
            "status": "available",
            "updated": payload.get("updated"),
            "dimension_ids": dimension_ids,
            "dimensions": dimension_summary,
            "target_regions": target_regions,
            "target_region_count": sum(len(values) for values in target_regions.values()),
        })

    return {
        "status": "available" if all(item["status"] == "available" for item in results) else "partial",
        "sources": results,
        "ready_for_parser_design": all(
            item["status"] == "available"
            and item.get("target_region_count", 0) > 0
            for item in results
        ),
    }


def fetch_regional_housing_evidence(
    adapter: EurostatAdapter,
) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    diagnostics: list[dict] = []

    for config in REGIONAL_HOUSING_SERIES:
        payload = adapter.fetch_dataset(
            config["dataset_id"],
            config["filters"],
        )
        normalized = normalize_subnational(
            adapter,
            config,
            payload,
        )
        rows.extend(normalized)
        diagnostics.append({
            "indicator_id": config["indicator_id"],
            "dataset_id": config["dataset_id"],
            "row_count": len(normalized),
            "regions": sorted({row["geo_code"] for row in normalized}),
            "latest_period": max(
                (row["period"] for row in normalized),
                default=None,
            ),
            "updated": payload.get("updated"),
        })

    return rows, diagnostics
