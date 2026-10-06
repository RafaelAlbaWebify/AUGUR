from __future__ import annotations

from datetime import datetime, timezone
from itertools import product

from app.ingestion.eurostat import EurostatAdapter


SOURCE_ID = "EUROSTAT"
TARGET_PREFIXES = {"ES", "PT", "IE"}

REGIONAL_LABOUR_SERIES = [
    {
        "indicator_id": "regional_employment_rate",
        "dataset_id": "lfst_r_lfe2emprt",
        "filters": {
            "freq": "A",
            "unit": "PC",
            "age": "Y15-64",
            "sex": "T",
            "geoLevel": "nuts2",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "regional_unemployment_rate",
        "dataset_id": "lfst_r_lfu3rt",
        "filters": {
            "freq": "A",
            "unit": "PC",
            "age": "Y15-74",
            "sex": "T",
            "isced11": "TOTAL",
            "geoLevel": "nuts2",
        },
        "unit": "percent",
    },
]


def normalize_subnational(
    adapter: EurostatAdapter,
    config: dict,
    payload: dict,
    target_prefixes: set[str] | None = None,
) -> list[dict]:
    prefixes = target_prefixes or TARGET_PREFIXES
    dimension_ids = payload["id"]
    dimension_sizes = payload["size"]
    dimensions = payload["dimension"]
    raw_values = payload["value"]

    dimension_codes = [
        adapter._ordered_codes(dimensions[dimension_id])
        for dimension_id in dimension_ids
    ]
    geo_labels = adapter._category_labels(dimensions.get("geo", {}))
    retrieved_at = datetime.now(timezone.utc)
    rows: list[dict] = []

    for coordinates in product(*[range(size) for size in dimension_sizes]):
        flat_index = 0
        multiplier = 1
        for coordinate, size in zip(
            reversed(coordinates),
            reversed(dimension_sizes),
        ):
            flat_index += coordinate * multiplier
            multiplier *= size

        if isinstance(raw_values, list):
            value = (
                raw_values[flat_index]
                if flat_index < len(raw_values)
                else None
            )
        else:
            value = raw_values.get(str(flat_index))
            if value is None:
                value = raw_values.get(flat_index)

        if value is None:
            continue

        labels = {
            dimension_id: dimension_codes[index][coordinates[index]]
            for index, dimension_id in enumerate(dimension_ids)
        }
        geo_code = str(labels.get("geo") or "")
        period = str(labels.get("time") or "")

        if (
            len(geo_code) != 4
            or geo_code[:2] not in prefixes
            or not period.isdigit()
        ):
            continue

        rows.append(
            {
                "geo_code": geo_code,
                "geo_name": geo_labels.get(geo_code, geo_code),
                "geo_level": "NUTS2",
                "indicator_id": config["indicator_id"],
                "period": int(period),
                "value": float(value),
                "unit": config["unit"],
                "source_id": SOURCE_ID,
                "dataset_id": config["dataset_id"],
                "retrieved_at": retrieved_at,
                "source_updated_at": payload.get("updated"),
            }
        )

    return rows


def fetch_regional_labour(
    adapter: EurostatAdapter,
) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    diagnostics: list[dict] = []

    for config in REGIONAL_LABOUR_SERIES:
        payload = adapter.fetch_dataset(
            config["dataset_id"],
            config["filters"],
        )
        normalized = normalize_subnational(adapter, config, payload)
        rows.extend(normalized)
        diagnostics.append(
            {
                "indicator_id": config["indicator_id"],
                "dataset_id": config["dataset_id"],
                "row_count": len(normalized),
                "regions": sorted({row["geo_code"] for row in normalized}),
                "latest_period": max(
                    (row["period"] for row in normalized),
                    default=None,
                ),
                "updated": payload.get("updated"),
            }
        )

    return rows, diagnostics
