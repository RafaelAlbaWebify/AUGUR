from __future__ import annotations

from collections import Counter
import httpx


PM25_ANNUAL_MEAN_QUERY_URL = (
    "https://air.discomap.eea.europa.eu/arcgis/rest/services/"
    "Airbase/Particulate_matter_PM2_5/MapServer/1/query"
)
TARGET_COUNTRIES = {"ES", "PT", "IE"}


def inspect_eea_pm25(
    client: httpx.Client | None = None,
) -> dict:
    owns_client = client is None
    active = client or httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1 EEA PM2.5 source inspector"},
    )

    params = {
        "where": "country_iso_code IN ('ES','PT','IE')",
        "outFields": (
            "station_european_code,country_iso_code,station_name,"
            "station_type_of_area,station_longitude_deg,station_latitude_deg,"
            "statistics_year,statistic_value,statistics_percentage_valid,"
            "measurement_unit"
        ),
        "returnGeometry": "false",
        "orderByFields": "statistics_year DESC",
        "resultRecordCount": 2000,
        "f": "json",
    }

    try:
        response = active.get(PM25_ANNUAL_MEAN_QUERY_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    finally:
        if owns_client:
            active.close()

    if payload.get("error"):
        return {
            "status": "unavailable",
            "error": payload["error"],
            "ready_for_aggregation_design": False,
        }

    features = payload.get("features") or []
    records = [feature.get("attributes", {}) for feature in features]

    years = sorted(
        {
            int(row["statistics_year"])
            for row in records
            if row.get("statistics_year") is not None
        },
        reverse=True,
    )
    latest_year = years[0] if years else None
    latest = [
        row for row in records
        if latest_year is not None
        and row.get("statistics_year") == latest_year
    ]

    countries = Counter(
        str(row.get("country_iso_code") or "")
        for row in latest
    )
    valid_coordinates = sum(
        1
        for row in latest
        if row.get("station_longitude_deg") is not None
        and row.get("station_latitude_deg") is not None
    )
    values = [
        float(row["statistic_value"])
        for row in latest
        if row.get("statistic_value") is not None
    ]

    return {
        "status": "available" if latest else "empty",
        "source": "EEA Air Quality Statistics",
        "pollutant": "PM2.5",
        "metric": "annual_mean_concentration",
        "unit": sorted(
            {
                str(row.get("measurement_unit"))
                for row in latest
                if row.get("measurement_unit")
            }
        ),
        "latest_year": latest_year,
        "available_years_sample": years[:10],
        "latest_record_count": len(latest),
        "latest_records_by_country": dict(sorted(countries.items())),
        "latest_valid_coordinate_count": valid_coordinates,
        "latest_value_min": min(values) if values else None,
        "latest_value_max": max(values) if values else None,
        "sample_records": latest[:5],
        "ready_for_aggregation_design": bool(
            latest
            and valid_coordinates == len(latest)
            and all(countries.get(code, 0) > 0 for code in TARGET_COUNTRIES)
        ),
        "notes": [
            "Station observations are point evidence and are not NUTS2 values.",
            "A regional value requires an explicit spatial assignment and aggregation method.",
            "Traffic, urban-background and rural stations should not be silently treated as equivalent population exposure.",
        ],
    }
