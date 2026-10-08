from __future__ import annotations

import csv
import io
import json

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_FUA_TERR@DF_DENSITY"
DATASET_VERSION = "1.1"
URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_FUA_TERR@DF_DENSITY,1.1/"
    ".A.POP_DEN.."
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
        diagnostics["response_preview"] = response.text[:1000]
        print(json.dumps(diagnostics, indent=2))
        return 2

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    city_name_tokens = (
        "sydney",
        "melbourne",
        "brisbane",
        "perth",
        "adelaide",
        "canberra",
        "hobart",
        "darwin",
    )
    australian_rows = [
        row
        for row in rows
        if (
            str(row.get("REF_AREA") or "").upper().startswith(("AU", "AUS"))
            or any(
                token in str(row.get("Reference area") or "").lower()
                for token in city_name_tokens
            )
        )
    ]
    australian_refs = sorted({
        str(row.get("REF_AREA") or "")
        for row in australian_rows
        if row.get("REF_AREA")
    })

    diagnostics.update({
        "headers": reader.fieldnames or [],
        "row_count": len(rows),
        "australian_row_count": len(australian_rows),
        "australian_reference_count": len(australian_refs),
        "australian_reference_areas": australian_refs[:80],
        "global_reference_sample": sorted({
            str(row.get("REF_AREA") or "")
            for row in rows
            if row.get("REF_AREA")
        })[:120],
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
        "sample_rows": [
            {
                "reference": row.get("REF_AREA"),
                "name": row.get("Reference area"),
                "frequency": row.get("FREQ"),
                "measure": row.get("MEASURE"),
                "unit": row.get("UNIT_MEASURE"),
                "time": row.get("TIME_PERIOD"),
                "value": row.get("OBS_VALUE"),
                "country": row.get("COUNTRY"),
            }
            for row in australian_rows[:20]
        ],
        "ready_for_parser_design": bool(australian_rows),
    })

    print(json.dumps(diagnostics, indent=2, default=str))
    return 0 if australian_rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
