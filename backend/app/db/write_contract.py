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


def validate_specialized_batch(
    rows: list[dict], *, key_fields: tuple[str, ...],
    required_numeric_fields: tuple[str, ...] = (),
    optional_numeric_fields: tuple[str, ...] = (),
) -> None:
    """Fail before DB access if a specialized source batch contains ambiguous keys or values.

    Key tuple must match the actual DuckDB primary key; source-specific semantic
    and quality policies remain the adapter's responsibility.
    """
    seen: set[tuple] = set()
    for index, row in enumerate(rows):
        key = []
        for field in key_fields:
            value = row.get(field)
            if value is None or isinstance(value, bool) or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"Missing specialized key {field} at row {index}")
            key.append(value.strip().upper() if isinstance(value, str) else value)
        identity = tuple(key)
        if identity in seen:
            raise ValueError(f"Duplicate specialized write key at row {index}: {identity}")
        seen.add(identity)
        for field in (*required_numeric_fields, *optional_numeric_fields):
            value = row.get(field)
            if field in optional_numeric_fields and value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"Invalid specialized numeric field {field} at row {index}")
