from __future__ import annotations

from time import monotonic

import httpx

from app.ingestion.eea_air_quality_api import API_BASE, TARGET_COUNTRIES
from app.ingestion.gisco_cities import (
    gisco_city_catalog,
    match_eea_cities_to_gisco,
)


GISCO_CITIES_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/urau/geojson/"
    "URAU_LB_2024_4326_CITIES.geojson"
)
CACHE_TTL_SECONDS = 24 * 60 * 60
_CACHE: tuple[float, dict[str, dict]] | None = None


def eea_city_mapping(
    client: httpx.Client | None = None,
    force_refresh: bool = False,
) -> dict[str, dict]:
    global _CACHE

    if (
        not force_refresh
        and _CACHE is not None
        and monotonic() - _CACHE[0] < CACHE_TTL_SECONDS
    ):
        return _CACHE[1]

    owns_client = client is None
    active = client or httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1 EEA city mapping"},
    )
    try:
        gisco_response = active.get(GISCO_CITIES_URL)
        gisco_response.raise_for_status()
        eea_response = active.post(
            f"{API_BASE}/City",
            json=TARGET_COUNTRIES,
        )
        eea_response.raise_for_status()

        gisco = gisco_city_catalog(
            gisco_response.json(),
            set(TARGET_COUNTRIES),
        )
        match = match_eea_cities_to_gisco(
            gisco,
            eea_response.json(),
        )
    finally:
        if owns_client:
            active.close()

    mapping = {
        row["city_code"]: row
        for row in match["matched"]
    }
    _CACHE = (monotonic(), mapping)
    return mapping


def resolve_eea_city(
    city_code: str,
    client: httpx.Client | None = None,
) -> dict | None:
    return eea_city_mapping(client=client).get(city_code.upper())
