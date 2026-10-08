from __future__ import annotations

import csv
import io
import json

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_FUA_TRAN@DF_PT_ACCESS"
DATASET_VERSION = "1.1"
URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_FUA_TRAN@DF_PT_ACCESS,1.1/"
    "AUS01F+AUS02F.A......"
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
        "modes": sorted({
            row.get("MODE")
            for row in rows
            if row.get("MODE")
        }),
        "services": sorted({
            row.get("SERVICE")
            for row in rows
            if row.get("SERVICE")
        }),
        "travel_times": sorted({
            row.get("TRAVEL_TIME")
            for row in rows
            if row.get("TRAVEL_TIME")
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
                "mode": row.get("MODE"),
                "mode_label": row.get("Mode of transport"),
                "travel_time": row.get("TRAVEL_TIME"),
                "travel_time_label": row.get("Travel time"),
                "service": row.get("SERVICE"),
                "service_label": row.get("Service"),
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
