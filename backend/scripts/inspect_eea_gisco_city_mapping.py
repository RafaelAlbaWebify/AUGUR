from __future__ import annotations

import json

import httpx

from app.ingestion.eea_air_quality_api import API_BASE, TARGET_COUNTRIES
from app.ingestion.gisco_cities import gisco_city_catalog, match_eea_cities_to_gisco


GISCO_CITIES_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/urau/geojson/"
    "URAU_LB_2024_4326_CITIES.geojson"
)


def main() -> int:
    with httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1 city catalog inspector"},
    ) as client:
        gisco_response = client.get(GISCO_CITIES_URL)
        gisco_response.raise_for_status()
        eea_response = client.post(
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

    focus_names = {"oviedo", "vigo", "dublin"}
    focus = [
        row for row in match["matched"]
        if row["eea_city_name"].casefold() in focus_names
    ]
    gisco_diagnostics = [
        row for row in gisco
        if row["country_code"] in {"IE", "PT"}
    ]

    print(json.dumps({
        "status": "available",
        "gisco_city_count": len(gisco),
        "eea_city_count": len(eea_response.json()),
        "matched_count": match["matched_count"],
        "unmatched_count": match["unmatched_count"],
        "ambiguous_count": match["ambiguous_count"],
        "focus": focus,
        "gisco_ie_pt_catalog": gisco_diagnostics,
        "unmatched_sample": match["unmatched"][:20],
        "ambiguous": match["ambiguous"],
    }, indent=2, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
