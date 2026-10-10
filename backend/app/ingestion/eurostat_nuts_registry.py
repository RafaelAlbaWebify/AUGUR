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
            matched = unmatched = observed_matched = observed_unmatched = 0
            for country, entries in item.get("countries", {}).items():
                rows = []
                for entry in entries:
                    row = dict(entry)
                    is_member = row["geo_code"] in official_codes
                    observed = row.get("observation_status") == "observed"
                    row["nuts_2024_status"] = "official_nuts2_2024" if is_member else "not_in_nuts2_2024"
                    matched += int(is_member)
                    unmatched += int(not is_member)
                    observed_matched += int(is_member and observed)
                    observed_unmatched += int((not is_member) and observed)
                    rows.append(row)
                by_country[country] = rows
            item["countries"] = by_country
            item["official_nuts2024_region_count"] = matched
            item["outside_nuts2024_count"] = unmatched
            item["official_nuts2024_observed_region_count"] = observed_matched
            item["outside_nuts2024_observed_region_count"] = observed_unmatched
        results.append(item)
    return {
        **report,
        "nuts_registry": {"authority": "Eurostat GISCO", "vintage": 2024,
                          "level": 2, "source_url": NUTS_2024_GEOJSON,
                          "registry_count": len(official_codes)},
        "datasets": results,
        "registry_reconciled": True,
    }


def assess_reconciled_live_coverage(report: dict) -> dict:
    """Fail closed unless every configured dataset has observed official NUTS2 data."""
    if report.get("registry_reconciled") is not True:
        raise ValueError("Coverage report must be reconciled with the official NUTS registry")

    datasets = []
    failures = []
    for item in report.get("datasets", []):
        outside_observed_codes = sorted(
            row["geo_code"]
            for entries in item.get("countries", {}).values()
            for row in entries
            if row.get("nuts_2024_status") == "not_in_nuts2_2024"
            and row.get("observation_status") == "observed"
        )
        official_count = item.get("official_nuts2024_region_count", 0)
        official_observed = item.get("official_nuts2024_observed_region_count", 0)
        summary = {
            "dataset_id": item.get("dataset_id"),
            "status": item.get("status"),
            "country_count": item.get("country_count", 0),
            "region_count": item.get("region_count", 0),
            "observed_region_count": item.get("observed_region_count", 0),
            "official_nuts2024_region_count": official_count,
            "official_nuts2024_observed_region_count": official_observed,
            "official_nuts2024_without_observation_count": max(0, official_count - official_observed),
            "outside_nuts2024_count": item.get("outside_nuts2024_count", 0),
            "outside_nuts2024_observed_region_count": item.get("outside_nuts2024_observed_region_count", 0),
            "outside_nuts2024_observed_codes": outside_observed_codes,
            "source_updated_at": item.get("source_updated_at"),
        }
        datasets.append(summary)
        if item.get("status") != "available":
            failures.append(f"{item.get('dataset_id')}: source unavailable")
        elif summary["official_nuts2024_observed_region_count"] <= 0:
            failures.append(f"{item.get('dataset_id')}: no observed official NUTS2 2024 regions")

    if not datasets:
        failures.append("no datasets were evaluated")

    return {
        "ready": not failures,
        "registry": report.get("nuts_registry"),
        "datasets": datasets,
        "failures": failures,
    }
