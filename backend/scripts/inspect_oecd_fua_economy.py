from __future__ import annotations

import csv
import io
import json

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_FUA_ECO@DF_ECONOMY"
DATASET_VERSION = "1.1"
URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_FUA_ECO@DF_ECONOMY,1.1/"
    "AUS01F+AUS02F.A..."
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
        if (
            response.status_code == 404
            and "NoRecordsFound" in response.text
        ):
            diagnostics["status"] = "coverage_gap_for_probe_geographies"
            diagnostics["ready_for_parser_design"] = False
            diagnostics["notes"] = [
                "The OECD FUA economy dataset is valid, but the probed Australian FUAs return no records.",
                "AUGUR treats this as a source coverage gap and does not infer economic values from regional data.",
            ]
            print(json.dumps(diagnostics, indent=2))
            return 0
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
        "references": sorted({
            row.get("REF_AREA")
            for row in rows
            if row.get("REF_AREA")
        }),
        "territorial_levels": sorted({
            row.get("TERRITORIAL_LEVEL")
            for row in rows
            if row.get("TERRITORIAL_LEVEL")
        }),
        "sample_rows": [
            {
                "reference": row.get("REF_AREA"),
                "name": row.get("Reference area"),
                "measure": row.get("MEASURE"),
                "measure_label": row.get("Measure"),
                "unit": row.get("UNIT_MEASURE"),
                "unit_label": row.get("Unit of measure"),
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
