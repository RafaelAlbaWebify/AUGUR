from __future__ import annotations

import argparse

import httpx

from app.catalog import COUNTRIES
from app.db.bootstrap import initialize_datastores
from app.db.analytics import subnational_storage_status
from app.services.regional_evidence import regional_evidence


NUTS3_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_20M_2024_4326_LEVL_3.geojson"
)
DEFAULT_COUNTRIES = ["ESP", "PRT", "IRL"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize NUTS3 safety evidence into DuckDB."
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=DEFAULT_COUNTRIES,
    )
    args = parser.parse_args()

    country_by_iso3 = {country["iso3"]: country for country in COUNTRIES}
    requested = [value.upper() for value in args.countries]
    unknown = [code for code in requested if code not in country_by_iso3]
    if unknown:
        raise SystemExit(f"Unsupported countries: {', '.join(unknown)}")

    initialize_datastores()

    with httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        response = client.get(NUTS3_URL)
        response.raise_for_status()
        payload = response.json()

    any_country_empty = False

    for iso3 in requested:
        iso2 = country_by_iso3[iso3]["iso2"]
        codes = sorted({
            str(feature.get("properties", {}).get("NUTS_ID", "")).upper()
            for feature in payload.get("features", [])
            if feature.get("properties", {}).get("CNTR_CODE") == iso2
            and len(str(feature.get("properties", {}).get("NUTS_ID", ""))) == 5
        })

        with_data = 0
        observation_count = 0
        print()
        print("=" * 72)
        print(f"AUGUR NUTS3 SAFETY SYNC · {iso3}")
        print("=" * 72)
        print(f"NUTS3 regions discovered: {len(codes)}")

        for index, code in enumerate(codes, start=1):
            result = regional_evidence(code, force_refresh=True)
            available = int(result.get("available_count", 0))
            observation_count += available
            if available:
                with_data += 1
            print(
                f"  region {index:>3}/{len(codes):<3} "
                f"{code:<6} available={available}/{result.get('indicator_count', 0)}"
            )

        print(
            f"Stored safety coverage: {with_data}/{len(codes)} regions "
            f"({observation_count} latest series)"
        )
        if codes and with_data == 0:
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
