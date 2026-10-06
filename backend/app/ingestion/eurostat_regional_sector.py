from __future__ import annotations

from datetime import datetime, timezone
from itertools import product

from app.ingestion.eurostat import EurostatAdapter


SOURCE_ID = "EUROSTAT"
DATASET_ID = "lfst_r_lfe2en2"
TARGET_PREFIXES = {"ES", "PT", "IE"}

# Keep the total plus single-section NACE codes. Aggregated multi-section
# groupings are excluded to avoid double-counting sector structure.
ALLOWED_NACE_CODES = {"TOTAL"} | {chr(code) for code in range(ord("A"), ord("U") + 1)}


def normalize_regional_sector_employment(
    adapter: EurostatAdapter,
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
    nace_labels = adapter._category_labels(dimensions.get("nace_r2", {}))
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
        nace_code = str(labels.get("nace_r2") or "")

        if (
            len(geo_code) != 4
            or geo_code[:2] not in prefixes
            or not period.isdigit()
            or nace_code not in ALLOWED_NACE_CODES
        ):
            continue

        rows.append(
            {
                "geo_code": geo_code,
                "geo_name": geo_labels.get(geo_code, geo_code),
                "geo_level": "NUTS2",
                "period": int(period),
                "nace_code": nace_code,
                "nace_label": nace_labels.get(nace_code, nace_code),
                "employment_thousands": float(value),
                "source_id": SOURCE_ID,
                "dataset_id": DATASET_ID,
                "retrieved_at": retrieved_at,
                "source_updated_at": payload.get("updated"),
            }
        )

    return rows


def fetch_regional_sector_employment(
    adapter: EurostatAdapter,
) -> tuple[list[dict], dict]:
    filters = {
        "freq": "A",
        "unit": "THS_PER",
        "age": "Y15-64",
        "sex": "T",
        "geoLevel": "nuts2",
    }
    payload = adapter.fetch_dataset(DATASET_ID, filters)
    rows = normalize_regional_sector_employment(adapter, payload)

    return rows, {
        "dataset_id": DATASET_ID,
        "row_count": len(rows),
        "region_count": len({row["geo_code"] for row in rows}),
        "nace_codes": sorted({row["nace_code"] for row in rows}),
        "latest_period": max((row["period"] for row in rows), default=None),
        "updated": payload.get("updated"),
    }
