"""Common fail-closed validation for persistent observation write batches.

Do not infer provider-specific dimensions; upstream source contracts own those.
"""
from __future__ import annotations

import math


def validate_write_batch(rows: list[dict], *, subnational: bool) -> None:
    seen: set[tuple] = set()
    keys = ("geography_system", "geo_code", "indicator_id", "period", "source_id") if subnational else ("country_iso3", "indicator_id", "period", "source_id")
    for offset, row in enumerate(rows):
        value = row.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"Invalid observation value at row {offset}")
        period = row.get("period")
        if isinstance(period, bool) or not isinstance(period, int):
            raise ValueError(f"Invalid observation period at row {offset}")
        for name in ("indicator_id", "source_id", "dataset_id"):
            if not isinstance(row.get(name), str) or not row[name].strip():
                raise ValueError(f"Missing observation {name} at row {offset}")
        if subnational:
            from app.db.analytics import _subnational_geography_system
            code = row.get("geo_code")
            if not isinstance(code, str) or not code.strip() or not isinstance(row.get("geo_level"), str) or not row["geo_level"].strip():
                raise ValueError(f"Invalid subnational geography at row {offset}")
            identity = (_subnational_geography_system(row), code.upper(), row["indicator_id"], period, row["source_id"])
        else:
            country = row.get("country_iso3")
            if not isinstance(country, str) or len(country) != 3 or not country.isalpha():
                raise ValueError(f"Invalid national geography at row {offset}")
            identity = (country.upper(), row["indicator_id"], period, row["source_id"])
            if not isinstance(row.get("observation_type"), str) or not row["observation_type"]:
                raise ValueError(f"Missing observation_type at row {offset}")
        if identity in seen:
            raise ValueError(f"Duplicate observation write key at row {offset}: {identity}")
        seen.add(identity)
