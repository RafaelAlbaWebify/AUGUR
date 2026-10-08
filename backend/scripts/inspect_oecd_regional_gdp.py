from __future__ import annotations

import csv
import io
import json

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_REG_ECO@DF_GDP"
DATASET_VERSION = "2.4"
URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_ECO@DF_GDP,2.4/"
    "A.TL2.AU1+AU2..GDP..Q.USD_PPP_PS"
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
        "price_bases": sorted({
            row.get("PRICE_BASE")
            for row in rows
            if row.get("PRICE_BASE")
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
        "sample_rows": [
            {
                "reference": row.get("REF_AREA"),
                "name": row.get("Reference area"),
                "level": row.get("TERRITORIAL_LEVEL"),
                "measure": row.get("MEASURE"),
                "price_base": row.get("PRICE_BASE"),
                "unit": row.get("UNIT_MEASURE"),
                "unit_label": row.get("Unit of measure"),
                "time": row.get("TIME_PERIOD"),
                "value": row.get("OBS_VALUE"),
                "country": row.get("COUNTRY"),
            }
            for row in rows[:20]
        ],
        "ready_for_parser_design": bool(rows),
    })

    print(json.dumps(diagnostics, indent=2, default=str))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
