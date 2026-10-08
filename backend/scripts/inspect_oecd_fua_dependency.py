from __future__ import annotations

import csv
import io
import json

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_FUA_DEMO@DF_DEPEND"
DATASET_VERSION = "1.2"
URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_FUA_DEMO@DF_DEPEND,1.2/"
    ".A......."
)
PARAMS = {
    "startPeriod": "2021",
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
        diagnostics["response_preview"] = response.text[:1000]
        print(json.dumps(diagnostics, indent=2))
        return 2

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    australian_rows = [
        row
        for row in rows
        if str(row.get("REF_AREA") or "").upper().startswith("AUS")
    ]

    diagnostics.update({
        "headers": reader.fieldnames or [],
        "row_count": len(rows),
        "australian_row_count": len(australian_rows),
        "australian_reference_count": len({
            row.get("REF_AREA")
            for row in australian_rows
            if row.get("REF_AREA")
        }),
        "ages": sorted({
            row.get("AGE")
            for row in australian_rows
            if row.get("AGE")
        }),
        "measures": sorted({
            row.get("MEASURE")
            for row in australian_rows
            if row.get("MEASURE")
        }),
        "units": sorted({
            row.get("UNIT_MEASURE")
            for row in australian_rows
            if row.get("UNIT_MEASURE")
        }),
        "territorial_levels": sorted({
            row.get("TERRITORIAL_LEVEL")
            for row in australian_rows
            if row.get("TERRITORIAL_LEVEL")
        }),
        "sample_rows": [
            {
                "reference": row.get("REF_AREA"),
                "name": row.get("Reference area"),
                "age": row.get("AGE"),
                "age_label": row.get("Age"),
                "measure": row.get("MEASURE"),
                "measure_label": row.get("Measure"),
                "unit": row.get("UNIT_MEASURE"),
                "unit_label": row.get("Unit of measure"),
                "level": row.get("TERRITORIAL_LEVEL"),
                "level_label": row.get("Territorial level"),
                "time": row.get("TIME_PERIOD"),
                "value": row.get("OBS_VALUE"),
            }
            for row in australian_rows[:30]
        ],
        "ready_for_parser_design": bool(australian_rows),
    })

    print(json.dumps(diagnostics, indent=2, default=str))
    return 0 if australian_rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
