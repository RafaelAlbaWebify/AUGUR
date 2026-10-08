from __future__ import annotations

import csv
import io
import json

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_FUA_ENV@DF_POLLUTION"
DATASET_VERSION = "1.5"
URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_FUA_ENV@DF_POLLUTION,1.5/"
    "AUS01F+AUS02F+AUS01C+AUS02C.A.PM25_POP_EXP.MCG_M3...."
)
PARAMS = {
    "startPeriod": "2020",
    "dimensionAtObservation": "AllDimensions",
    "format": "csvfilewithlabels",
}


def main() -> int:
    with httpx.Client(
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        response = client.get(URL, params=PARAMS)

    diagnostics = {
        "source_id": SOURCE_ID,
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "request_url": str(response.request.url),
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "response_bytes": len(response.content),
    }

    if response.status_code >= 400:
        diagnostics["response_preview"] = response.text[:1200]
        print(json.dumps(diagnostics, indent=2))
        return 2

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)

    diagnostics.update({
        "headers": reader.fieldnames or [],
        "row_count": len(rows),
        "measures": sorted({
            row.get("MEASURE")
            for row in rows
            if row.get("MEASURE")
        }),
        "units": sorted({
            row.get("UNIT_MEASURE")
            for row in rows
            if row.get("UNIT_MEASURE")
        }),
        "territorial_levels": sorted({
            row.get("TERRITORIAL_LEVEL")
            for row in rows
            if row.get("TERRITORIAL_LEVEL")
        }),
        "unit_multipliers": sorted({
            row.get("UNIT_MULT")
            for row in rows
            if row.get("UNIT_MULT")
        }),
        "time_seasons": sorted({
            row.get("TIME_SEASON")
            for row in rows
            if row.get("TIME_SEASON")
        }),
        "designations": sorted({
            row.get("DESIGNATION")
            for row in rows
            if row.get("DESIGNATION")
        }),
        "observation_statuses": sorted({
            row.get("OBS_STATUS")
            for row in rows
            if row.get("OBS_STATUS")
        }),
        "references": sorted({
            row.get("REF_AREA")
            for row in rows
            if row.get("REF_AREA")
        }),
        "sample_rows": [
            {
                "reference": row.get("REF_AREA"),
                "name": row.get("Reference area"),
                "measure": row.get("MEASURE"),
                "measure_label": row.get("Measure"),
                "unit": row.get("UNIT_MEASURE"),
                "unit_label": row.get("Unit of measure"),
                "pollutant_level": row.get("POLLUTANT_CONCENTRATION"),
                "pollutant_level_label": row.get("Pollutant concentration level"),
                "time_season": row.get("TIME_SEASON"),
                "time_season_label": row.get("Time of the day and season"),
                "designation": row.get("DESIGNATION"),
                "designation_label": row.get("IUCN management categories"),
                "unit_multiplier": row.get("UNIT_MULT"),
                "unit_multiplier_label": row.get("Unit multiplier"),
                "obs_status": row.get("OBS_STATUS"),
                "level": row.get("TERRITORIAL_LEVEL"),
                "level_label": row.get("Territorial level"),
                "time": row.get("TIME_PERIOD"),
                "value": row.get("OBS_VALUE"),
            }
            for row in rows[:30]
        ],
        "ready_for_parser_design": bool(rows),
    })

    print(json.dumps(diagnostics, indent=2, default=str))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
