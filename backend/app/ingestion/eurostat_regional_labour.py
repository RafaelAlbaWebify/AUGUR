from __future__ import annotations

from datetime import datetime, timezone
from itertools import product

from app.ingestion.eurostat import EurostatAdapter
from app.services.regional_evidence import REGIONAL_INDICATORS


SOURCE_ID = "EUROSTAT"
TARGET_PREFIXES = {"ES", "PT", "IE"}

REGIONAL_LABOUR_SERIES = [
    {
        "indicator_id": "regional_employment_rate",
        "dataset_id": "lfst_r_lfe2emprt",
        "filters": {
            "freq": "A",
            "unit": "PC",
            "age": "Y20-64",
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
            "age": "Y20-64",
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
    prefixes = TARGET_PREFIXES if target_prefixes is None else {code.upper() for code in target_prefixes}
    if any(len(code) != 2 or not code.isalpha() for code in prefixes):
        raise ValueError('Country prefixes must be ISO2-like alphabetic codes')
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


def validate_labour_indicator_contracts() -> None:
    """Block silent drift from canonical indicator source/dimension definitions."""
    canonical = {item["indicator_id"]: item for item in REGIONAL_INDICATORS}
    for item in REGIONAL_LABOUR_SERIES:
        reference = canonical[item["indicator_id"]]
        if item["dataset_id"] != reference["dataset_id"] or item["unit"] != reference["unit"]:
            raise ValueError("Regional labour dataset or unit differs from canonical indicator")
        for key, expected in reference["filters"].items():
            if item["filters"].get(key) != expected:
                raise ValueError(f"Regional labour dimension contract mismatch: {item['indicator_id']} {key}")


def fetch_regional_labour(
    adapter: EurostatAdapter,
    target_prefixes: set[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    validate_labour_indicator_contracts()
    rows: list[dict] = []
    diagnostics: list[dict] = []

    for config in REGIONAL_LABOUR_SERIES:
        payload = adapter.fetch_dataset(
            config["dataset_id"],
            config["filters"],
        )
        normalized = normalize_subnational(adapter, config, payload, target_prefixes=target_prefixes)
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
