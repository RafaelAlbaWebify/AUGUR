from __future__ import annotations

from app.ingestion.eurostat import EurostatAdapter


SOURCES = [
    {
        "dataset_id": "isoc_r_iacc_h",
        "role": "regional_household_internet_access",
        "geo_level": "nuts2",
        "filters": {
            "freq": "A",
            "geoLevel": "nuts2",
            "time": "2025",
        },
    },
    {
        "dataset_id": "tran_r_avpa_nm",
        "role": "regional_air_passenger_throughput",
        "geo_level": "nuts2",
        "filters": {
            "freq": "A",
            "geoLevel": "nuts2",
            "time": "2024",
        },
    },
    {
        "dataset_id": "crim_gen_reg",
        "role": "regional_police_recorded_crime",
        "geo_level": "nuts3",
        "filters": {
            "freq": "A",
            "geoLevel": "nuts3",
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
            for code, _position in sorted(index.items(), key=lambda item: item[1])
        ]
    return []


def inspect_regional_access_and_safety(
    adapter: EurostatAdapter,
) -> dict:
    results = []

    for config in SOURCES:
        try:
            payload = adapter.fetch_dataset(
                config["dataset_id"],
                config["filters"],
            )
        except Exception as exc:
            results.append({
                "dataset_id": config["dataset_id"],
                "role": config["role"],
                "geo_level": config["geo_level"],
                "status": "unavailable",
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue

        dimensions = payload.get("dimension", {})
        dimension_ids = payload.get("id", [])
        summary = {}

        for dimension_id in dimension_ids:
            dimension = dimensions.get(dimension_id, {})
            codes = _ordered_codes(dimension)
            labels = dimension.get("category", {}).get("label", {})
            summary[dimension_id] = {
                "label": dimension.get("label"),
                "code_count": len(codes),
                "sample_codes": codes[:40],
                "sample_labels": {
                    code: labels.get(code)
                    for code in codes[:40]
                },
            }

        geo_codes = _ordered_codes(dimensions.get("geo", {}))
        expected_length = 4 if config["geo_level"] == "nuts2" else 5
        target_regions = {
            prefix: [
                code for code in geo_codes
                if code.startswith(prefix)
                and len(code) == expected_length
                and not code.endswith("Z")
            ]
            for prefix in ("ES", "PT", "IE")
        }

        time_codes = _ordered_codes(dimensions.get("time", {}))

        results.append({
            "dataset_id": config["dataset_id"],
            "role": config["role"],
            "geo_level": config["geo_level"],
            "status": "available",
            "updated": payload.get("updated"),
            "dimension_ids": dimension_ids,
            "dimensions": summary,
            "target_regions": target_regions,
            "target_region_count": sum(len(v) for v in target_regions.values()),
            "latest_period": max(
                (int(code) for code in time_codes if str(code).isdigit()),
                default=None,
            ),
        })

    return {
        "status": (
            "available"
            if all(item["status"] == "available" for item in results)
            else "partial"
        ),
        "sources": results,
        "ready_for_parser_design": any(
            item["status"] == "available"
            and item.get("target_region_count", 0) > 0
            for item in results
        ),
        "notes": [
            "Internet-access and air-passenger evidence are access/connectivity context, not universal quality-of-life scores.",
            "Police-recorded crime is kept at its published NUTS3 level and is not silently copied or aggregated to NUTS2.",
            "Crime comparisons require explicit caveats for legal, reporting and police-recording differences.",
        ],
    }
