from __future__ import annotations

import csv
import io
import json

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_REG_SOC@DF_SAFETY"
DATASET_VERSION = "2.4"
URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_SOC@DF_SAFETY,2.4/"
    "A..AU1+AU2......CS_10P5PS"
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
    diagnostics.update({
        "headers": reader.fieldnames or [],
        "row_count": len(rows),
        "measures": sorted({
            str(row.get("MEASURE") or "")
            for row in rows
            if row.get("MEASURE")
        }),
        "measure_labels": sorted({
            (
                str(row.get("MEASURE") or ""),
                str(row.get("Measure") or ""),
            )
            for row in rows
            if row.get("MEASURE")
        }),
        "units": sorted({
            str(row.get("UNIT_MEASURE") or "")
            for row in rows
            if row.get("UNIT_MEASURE")
        }),
        "levels": sorted({
            str(row.get("TERRITORIAL_LEVEL") or "")
            for row in rows
            if row.get("TERRITORIAL_LEVEL")
        }),
        "sample_rows": [
            {
                "reference": row.get("REF_AREA"),
                "name": row.get("Reference area"),
                "level": row.get("TERRITORIAL_LEVEL"),
                "measure": row.get("MEASURE"),
                "measure_label": row.get("Measure"),
                "unit": row.get("UNIT_MEASURE"),
                "unit_label": row.get("Unit of measure"),
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
