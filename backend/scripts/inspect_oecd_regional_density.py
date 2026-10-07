from __future__ import annotations

import csv
import io
import json

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_REG_DEMO@DF_DENSITY"
DATASET_VERSION = "2.4"
BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_DEMO@DF_DENSITY,2.4/"
    "A.TL2..DE1+DE2....PS_KM2"
)

PARAMS = {
    "startPeriod": "2021",
    "dimensionAtObservation": "AllDimensions",
    "format": "csvfile",
}


def _first_present(record: dict, candidates: list[str]) -> str | None:
    for key in candidates:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def main() -> int:
    with httpx.Client(
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        response = client.get(BASE_URL, params=PARAMS)

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
    rows = []
    for index, row in enumerate(reader):
        rows.append(row)
        if index >= 4999:
            break

    headers = reader.fieldnames or []
    level_candidates = [
        "TERRITORIAL_LEVEL",
        "Territorial level",
        "TERR_LEVEL",
        "REGION_LEVEL",
    ]
    reference_candidates = [
        "REF_AREA",
        "Reference area",
        "REG_ID",
        "REGION",
    ]
    name_candidates = [
        "Reference area",
        "REF_AREA_LABEL",
        "REG_NAME",
        "Region",
    ]
    unit_candidates = [
        "UNIT_MEASURE",
        "Unit of measure",
        "UNIT",
    ]

    levels = sorted({
        value
        for row in rows
        if (value := _first_present(row, level_candidates))
    })
    references = sorted({
        value
        for row in rows
        if (value := _first_present(row, reference_candidates))
    })
    units = sorted({
        value
        for row in rows
        if (value := _first_present(row, unit_candidates))
    })

    diagnostics.update({
        "headers": headers,
        "sampled_row_count": len(rows),
        "territorial_levels": levels[:20],
        "reference_area_count_in_sample": len(references),
        "reference_area_sample": references[:30],
        "unit_sample": units[:20],
        "sample_rows": [
            {
                "reference": _first_present(row, reference_candidates),
                "name": _first_present(row, name_candidates),
                "level": _first_present(row, level_candidates),
                "time": row.get("TIME_PERIOD"),
                "value": row.get("OBS_VALUE"),
                "unit": _first_present(row, unit_candidates),
            }
            for row in rows[:12]
        ],
        "ready_for_parser_design": bool(rows and headers),
    })

    print(json.dumps(diagnostics, indent=2, default=str))
    return 0 if diagnostics["ready_for_parser_design"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
