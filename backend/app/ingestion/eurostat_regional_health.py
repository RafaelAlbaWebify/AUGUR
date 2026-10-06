from __future__ import annotations

from app.ingestion.eurostat import EurostatAdapter


DATASETS = [
    {
        "id": "hlth_silc_08_r",
        "role": "regional_unmet_medical_needs",
        "filters": {
            "freq": "A",
            "geoLevel": "nuts2",
            "time": "2025",
        },
    },
    {
        "id": "hlth_rs_bdsrg2",
        "role": "regional_hospital_beds",
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


def inspect_regional_health_sources(adapter: EurostatAdapter) -> dict:
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
                "sample_codes": codes[:40],
                "sample_labels": {
                    code: labels.get(code)
                    for code in codes[:40]
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
