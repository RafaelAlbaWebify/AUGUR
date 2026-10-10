"""Reconcile observed Eurostat candidate regions with official GISCO NUTS 2024."""
from __future__ import annotations

import httpx

NUTS_2024_GEOJSON = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_20M_2024_4326_LEVL_2.geojson"
)


def extract_official_nuts2_codes(geojson: dict) -> set[str]:
    if geojson.get("type") != "FeatureCollection" or not isinstance(geojson.get("features"), list):
        raise ValueError("Invalid official GISCO FeatureCollection")
    codes = set()
    for feature in geojson["features"]:
        props = feature.get("properties") or {}
        level = props.get("LEVL_CODE")
        code = props.get("NUTS_ID")
        if str(level) != "2" or not isinstance(code, str) or len(code) != 4:
            raise ValueError("Unexpected GISCO NUTS2 feature fields")
        codes.add(code)
    if not codes:
        raise ValueError("Empty official GISCO NUTS2 registry")
    return codes


def fetch_official_nuts2_codes(client: httpx.Client) -> set[str]:
    response = client.get(NUTS_2024_GEOJSON, timeout=90.0)
    response.raise_for_status()
    return extract_official_nuts2_codes(response.json())


def reconcile_nuts2024(report: dict, official_codes: set[str]) -> dict:
    """Annotate each dataset member without treating historical codes as current."""
    if not official_codes:
        raise ValueError("Official registry must not be empty")
    results = []
    for dataset in report.get("datasets", []):
        item = dict(dataset)
        if item.get("status") == "available":
            by_country = {}
            matched = unmatched = observed_matched = 0
            for country, entries in item.get("countries", {}).items():
                rows = []
                for entry in entries:
                    row = dict(entry)
                    is_member = row["geo_code"] in official_codes
                    row["nuts_2024_status"] = "official_nuts2_2024" if is_member else "not_in_nuts2_2024"
                    matched += int(is_member)
                    unmatched += int(not is_member)
                    observed_matched += int(is_member and row.get("observation_status") == "observed")
                    rows.append(row)
                by_country[country] = rows
            item["countries"] = by_country
            item["official_nuts2024_region_count"] = matched
            item["outside_nuts2024_count"] = unmatched
            item["official_nuts2024_observed_region_count"] = observed_matched
        results.append(item)
    return {
        **report,
        "nuts_registry": {"authority": "Eurostat GISCO", "vintage": 2024,
                          "level": 2, "source_url": NUTS_2024_GEOJSON,
                          "registry_count": len(official_codes)},
        "datasets": results,
        "registry_reconciled": True,
    }
