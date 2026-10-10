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


def discover_dataset_geographies(payload: dict, dataset_id: str) -> dict:
    dimension = payload.get("dimension", {}).get("geo", {})
    codes = _ordered_codes(dimension)
    labels = dimension.get("category", {}).get("label", {})
    countries: dict[str, list[dict]] = defaultdict(list)
    for code in codes:
        # A 4-character geography code is a candidate, not certified NUTS vintage.
        if len(code) == 4 and code[:2].isalpha() and code[2:].isalnum():
            countries[code[:2].upper()].append({
                "geo_code": code,
                "geo_name": labels.get(code, code),
                "geo_level": "NUTS2_CANDIDATE",
            })
    return {
        "dataset_id": dataset_id,
        "source_id": "EUROSTAT",
        "source_updated_at": payload.get("updated"),
        "classification_status": "dataset_member_not_verified_nuts_vintage",
        "country_count": len(countries),
        "region_count": sum(map(len, countries.values())),
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
        "scope": "eurostat_dataset_geography_membership_only",
        "datasets": results,
        "ready": bool(results) and all(x["status"] == "available" for x in results),
    }
