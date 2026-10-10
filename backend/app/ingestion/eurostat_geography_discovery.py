"""Discover published NUTS2-shaped geography codes in Eurostat JSON-stat datasets.

Dataset membership is not proof of a current official NUTS classification.
"""
from __future__ import annotations

from collections import defaultdict


def _ordered_codes(dimension: dict) -> list[str]:
    idx = dimension.get("category", {}).get("index", {})
    if isinstance(idx, list):
        return [str(x) for x in idx]
    if isinstance(idx, dict):
        return [str(k) for k, _ in sorted(idx.items(), key=lambda kv: kv[1])]
    return []


def _has_valid_numeric_observation(payload: dict, flat_index: int) -> bool:
    from math import isfinite
    values = payload.get("value", {})
    value = (values[flat_index] if flat_index < len(values) else None) if isinstance(values, list) else values.get(str(flat_index), values.get(flat_index))
    return type(value) in (int, float) and isfinite(value)


def observed_geo_codes(payload: dict) -> set[str]:
    """Resolve JSON-stat flat indices from declared dimensions and valid values."""
    ids = payload.get("id", [])
    sizes = payload.get("size", [])
    if not ids or len(ids) != len(sizes) or "geo" not in ids:
        return set()
    if any(not isinstance(size, int) or size <= 0 for size in sizes):
        return set()
    geo_index = ids.index("geo")
    codes = _ordered_codes(payload.get("dimension", {}).get("geo", {}))
    if len(codes) != sizes[geo_index]:
        return set()
    stride = 1
    for size in sizes[geo_index + 1:]:
        stride *= size
    total = 1
    for size in sizes:
        total *= size
    values = payload.get("value", {})
    indices = range(min(total, len(values))) if isinstance(values, list) else (
        int(k) for k in values if str(k).isdigit() and int(k) < total
    )
    return {
        codes[(index // stride) % sizes[geo_index]]
        for index in indices
        if _has_valid_numeric_observation(payload, index)
    }


def discover_dataset_geographies(payload: dict, dataset_id: str) -> dict:
    dimension = payload.get("dimension", {}).get("geo", {})
    codes = _ordered_codes(dimension)
    labels = dimension.get("category", {}).get("label", {})
    countries: dict[str, list[dict]] = defaultdict(list)
    observed = observed_geo_codes(payload)
    for code in codes:
        # A 4-character geography code is a candidate, not certified NUTS vintage.
        if len(code) == 4 and code[:2].isalpha() and code[2:].isalnum():
            countries[code[:2].upper()].append({
                "geo_code": code,
                "geo_name": labels.get(code, code),
                "geo_level": "NUTS2_CANDIDATE",
                "observation_status": "observed" if code in observed else "no_numeric_observation",
            })
    return {
        "dataset_id": dataset_id,
        "source_id": "EUROSTAT",
        "source_updated_at": payload.get("updated"),
        "classification_status": "dataset_member_not_verified_nuts_vintage",
        "country_count": len(countries),
        "region_count": sum(map(len, countries.values())),
        "observed_region_count": sum(1 for group in countries.values() for geo in group if geo["observation_status"] == "observed"),
        "countries": {key: sorted(value, key=lambda row: row["geo_code"])
                      for key, value in sorted(countries.items())},
    }


def discover_regional_dataset_coverage(adapter, configurations: list[dict]) -> dict:
    results = []
    for cfg in configurations:
        try:
            payload = adapter.fetch_dataset(cfg["dataset_id"], cfg["filters"])
            results.append({"status": "available", **discover_dataset_geographies(
                payload, cfg["dataset_id"])})
        except Exception as exc:
            results.append({
                "status": "source_error",
                "dataset_id": cfg["dataset_id"],
                "error": f"{type(exc).__name__}: {exc}",
            })
    return {
        "scope": "eurostat_dataset_geography_and_numeric_observation_coverage",
        "datasets": results,
        "ready": bool(results) and all(x["status"] == "available" for x in results),
    }
