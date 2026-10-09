"""Build a reproducible CI geography audit without private local databases.

This creates an isolated temporary DuckDB and ingests only the requested
official GISCO geography catalog. No synthetic statistical observations.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import httpx

GISCO_NUTS2 = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_4326_LEVL_2.geojson"
GISCO_NUTS3 = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_4326_LEVL_3.geojson"


def official_codes(features: list, countries: set[str]) -> dict:
    result: dict[str, set[str]] = {country: set() for country in countries}
    for feature in features:
        properties = feature.get("properties") or {}
        country = str(properties.get("CNTR_CODE") or "").upper()
        code = str(properties.get("NUTS_ID") or "").upper()
        if country in result and code:
            result[country].add(code)
    return {country: sorted(codes) for country, codes in sorted(result.items())}


def fetch_catalog(url: str, countries: set[str]) -> dict:
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    if payload.get("type") != "FeatureCollection":
        raise ValueError("Unexpected GISCO response format")
    return official_codes(payload.get("features") or [], countries)


def audit(countries: set[str]) -> dict:
    catalogs = {
        "nuts2": fetch_catalog(GISCO_NUTS2, countries),
        "nuts3": fetch_catalog(GISCO_NUTS3, countries),
    }
    return {
        "scope": "official_gisco_nuts_2024_catalog_only",
        "source_urls": {"nuts2": GISCO_NUTS2, "nuts3": GISCO_NUTS3},
        "warning": (
            "Catalog code counts are not observed statistical indicators, "
            "and no data coverage is inferred. Only selected countries and "
            "the retrieved GISCO boundary files are represented."
        ),
        "catalogs": {
            level: {
                country: {"count": len(codes), "codes": codes}
                for country, codes in levels.items()
            }
            for level, levels in catalogs.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit({"ES", "IE", "PT"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        level: {country: info["count"] for country, info in countries.items()}
        for level, countries in result["catalogs"].items()
    }, indent=2))


if __name__ == "__main__":
    main()
