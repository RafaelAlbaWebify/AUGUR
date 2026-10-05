from __future__ import annotations

import argparse
import re

import httpx

from app.catalog import COUNTRIES
from app.db.bootstrap import initialize_datastores
from app.db.analytics import subnational_storage_status
from app.services.city_evidence import city_evidence
from app.services.regional_evidence import regional_evidence


NUTS2_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_4326_LEVL_2.geojson"
CITIES_URL = "https://gisco-services.ec.europa.eu/distribution/v2/urau/geojson/URAU_LB_2024_4326_CITIES.geojson"
DEFAULT_COUNTRIES = ["ESP", "IRL"]
CITY_CODE_RE = re.compile(r"^[A-Z]{2}\d{3}C$")


def _fetch_geojson(client: httpx.Client, url: str) -> dict:
    response = client.get(url)
    response.raise_for_status()
    payload = response.json()
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"Unexpected GISCO response: {url}")
    return payload


def _city_code(feature: dict) -> str | None:
    candidates = []
    properties = feature.get("properties") or {}
    for key in ("URAU_CODE", "URAU_ID", "CITY_CODE", "CODE"):
        candidates.append(properties.get(key))
    candidates.append(feature.get("id"))
    candidates.extend(properties.values())

    for value in candidates:
        if not isinstance(value, str):
            continue
        code = value.upper()
        if CITY_CODE_RE.match(code):
            return code
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize AUGUR subnational evidence into DuckDB."
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=DEFAULT_COUNTRIES,
        help="ISO3 country codes. Default: ESP IRL",
    )
    args = parser.parse_args()

    country_by_iso3 = {country["iso3"]: country for country in COUNTRIES}
    requested = [value.upper() for value in args.countries]
    unknown = [code for code in requested if code not in country_by_iso3]
    if unknown:
        raise SystemExit(f"Unsupported countries: {', '.join(unknown)}")

    initialize_datastores()

    with httpx.Client(
        timeout=httpx.Timeout(60.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        print("Loading GISCO NUTS 2 and Urban Audit geography...")
        nuts2 = _fetch_geojson(client, NUTS2_URL)
        cities = _fetch_geojson(client, CITIES_URL)

    any_country_empty = False

    for iso3 in requested:
        country = country_by_iso3[iso3]
        iso2 = country["iso2"]

        region_codes = sorted({
            str(feature.get("properties", {}).get("NUTS_ID", "")).upper()
            for feature in nuts2.get("features", [])
            if feature.get("properties", {}).get("CNTR_CODE") == iso2
            and feature.get("properties", {}).get("NUTS_ID")
        })

        city_codes = sorted({
            code
            for feature in cities.get("features", [])
            if (code := _city_code(feature))
            and code.startswith(iso2)
        })

        print()
        print("=" * 72)
        print(f"AUGUR SUBNATIONAL SYNC · {iso3}")
        print("=" * 72)
        print(f"NUTS 2 regions discovered: {len(region_codes)}")
        print(f"Urban Audit cities discovered: {len(city_codes)}")

        region_with_data = 0
        region_observations = 0
        for index, code in enumerate(region_codes, start=1):
            result = regional_evidence(code, force_refresh=True)
            available = int(result.get("available_count", 0))
            region_observations += available
            if available:
                region_with_data += 1
            print(
                f"  region {index:>2}/{len(region_codes):<2} "
                f"{code:<6} available={available}/{result.get('indicator_count', 0)}"
            )

        city_with_data = 0
        city_observations = 0
        for index, code in enumerate(city_codes, start=1):
            result = city_evidence(code, force_refresh=True)
            available = int(result.get("available_count", 0))
            city_observations += available
            if available:
                city_with_data += 1
            print(
                f"  city   {index:>2}/{len(city_codes):<2} "
                f"{code:<7} available={available}/{result.get('indicator_count', 0)}"
            )

        print(
            f"Stored coverage: regions {region_with_data}/{len(region_codes)} "
            f"({region_observations} latest series), "
            f"cities {city_with_data}/{len(city_codes)} "
            f"({city_observations} latest series)"
        )

        if region_codes and region_with_data == 0:
            any_country_empty = True

    status = subnational_storage_status()
    print()
    print("=" * 72)
    print("AUGUR SUBNATIONAL STORE")
    print("=" * 72)
    print(f"geographies={status['geography_count']}")
    print(f"nuts2={status['nuts2_count']}")
    print(f"cities={status['city_count']}")
    print(f"observations={status['observation_count']}")

    return 2 if any_country_empty else 0


if __name__ == "__main__":
    raise SystemExit(main())
