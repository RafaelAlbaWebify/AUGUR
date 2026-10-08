from __future__ import annotations

import csv
import io
import json

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_REG_CLIM@DF_LAND_TEMP"
DATASET_VERSION = "2.4"
URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_CLIM@DF_LAND_TEMP,2.4/all"
)
PARAMS = {
    "startPeriod": "2019",
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
    target_rows = [
        row
        for row in rows
        if (
            str(row.get("COUNTRY") or "").upper() == "AUS"
            or str(row.get("REF_AREA") or "").upper().startswith("AU")
        )
        and str(row.get("TERRITORIAL_LEVEL") or "").upper() in {"TL2", "TL3"}
        and str(row.get("MEASURE") or "").upper() == "DAY_LAND_TEMP_YEARLY"
    ]

    diagnostics.update({
        "headers": reader.fieldnames or [],
        "row_count": len(rows),
        "australian_row_count": len(target_rows),
        "levels": sorted({
            row.get("TERRITORIAL_LEVEL")
            for row in target_rows
            if row.get("TERRITORIAL_LEVEL")
        }),
        "measures": sorted({
            row.get("MEASURE")
            for row in target_rows
            if row.get("MEASURE")
        }),
        "units": sorted({
            row.get("UNIT_MEASURE")
            for row in target_rows
            if row.get("UNIT_MEASURE")
        }),
        "sample_rows": [
            {
                "reference": row.get("REF_AREA"),
                "name": row.get("Reference area"),
                "country": row.get("COUNTRY"),
                "level": row.get("TERRITORIAL_LEVEL"),
                "measure": row.get("MEASURE"),
                "measure_label": row.get("Measure"),
                "unit": row.get("UNIT_MEASURE"),
                "unit_label": row.get("Unit of measure"),
                "time": row.get("TIME_PERIOD"),
                "value": row.get("OBS_VALUE"),
            }
            for row in target_rows[:30]
        ],
        "ready_for_parser_design": bool(target_rows),
    })

    print(json.dumps(diagnostics, indent=2, default=str))
    return 0 if target_rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
