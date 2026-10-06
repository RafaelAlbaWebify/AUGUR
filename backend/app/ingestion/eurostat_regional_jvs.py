from __future__ import annotations

from collections import Counter

from app.ingestion.eurostat import EurostatAdapter


DATASET_ID = "jvs_q_isco_r21"
REFERENCE_PERIOD = "2026-Q2"


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


def inspect_regional_jvs(
    adapter: EurostatAdapter,
    reference_period: str = REFERENCE_PERIOD,
) -> dict:
    attempts = [
        {
            "freq": "Q",
            "time": reference_period,
            "geoLevel": "nuts2",
            "indic_em": "JVR",
            "s_adj": "NSA",
            "sizeclas": "TOTAL",
        },
        {
            "freq": "Q",
            "time": reference_period,
            "geoLevel": "nuts2",
            "indic_em": "JVR",
            "s_adj": "NSA",
        },
        {
            "freq": "Q",
            "time": reference_period,
            "geoLevel": "nuts2",
            "indic_em": "JVR",
        },
    ]

    last_error = None
    payload = None
    used_filters = None

    for filters in attempts:
        try:
            payload = adapter.fetch_dataset(DATASET_ID, filters)
            used_filters = filters
            break
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"

    if payload is None:
        return {
            "status": "unavailable",
            "dataset_id": DATASET_ID,
            "reference_period": reference_period,
            "last_error": last_error,
            "ready_for_parser_implementation": False,
        }

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
            "sample_codes": codes[:20],
            "sample_labels": {
                code: labels.get(code)
                for code in codes[:20]
            },
        }

    geo_codes = _ordered_codes(dimensions.get("geo", {}))
    by_country = Counter(code[:2] for code in geo_codes if len(code) >= 4)

    target_regions = {
        "ESP": sorted(code for code in geo_codes if code.startswith("ES")),
        "PRT": sorted(code for code in geo_codes if code.startswith("PT")),
        "IRL": sorted(code for code in geo_codes if code.startswith("IE")),
    }

    isco_dimension = next(
        (
            dimension_id
            for dimension_id in dimension_ids
            if "isco" in dimension_id.lower()
        ),
        None,
    )
    isco_codes = (
        _ordered_codes(dimensions.get(isco_dimension, {}))
        if isco_dimension
        else []
    )

    return {
        "status": "available",
        "dataset_id": DATASET_ID,
        "reference_period": reference_period,
        "used_filters": used_filters,
        "updated": payload.get("updated"),
        "dimension_ids": dimension_ids,
        "dimensions": dimension_summary,
        "nuts2_region_count": len(geo_codes),
        "nuts2_counts_by_country_prefix": dict(sorted(by_country.items())),
        "target_regions": target_regions,
        "isco_dimension": isco_dimension,
        "isco_codes": isco_codes,
        "ready_for_parser_implementation": bool(
            geo_codes and isco_dimension and isco_codes
        ),
        "notes": [
            "This inspector does not write regional JVS data to DuckDB.",
            "Eurostat jvs_q_isco_r21 is a separate quarterly regional source from the experimental annual ISCO-3 dataset.",
            "Regional evidence must preserve its NUTS2 and ISCO granularity and must not be silently promoted to city-level evidence.",
        ],
    }
