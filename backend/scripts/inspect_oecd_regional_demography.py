from __future__ import annotations

import csv
import io
import json
from collections import defaultdict

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_REG_DEMO@DF_DEMO"
DATASET_VERSION = "2.0"
URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_DEMO@DF_DEMO,2.0/"
    "A..AU1+AU2..._T._T."
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

    measure_units: dict[str, set[str]] = defaultdict(set)
    latest_by_measure_region: dict[tuple[str, str], dict] = {}
    for row in rows:
        measure = str(row.get("MEASURE") or "")
        unit = str(row.get("UNIT_MEASURE") or "")
        region = str(row.get("REF_AREA") or "")
        period_text = str(row.get("TIME_PERIOD") or "")
        if measure and unit:
            measure_units[measure].add(unit)
        if not (measure and region and period_text.isdigit()):
            continue
        key = (measure, region)
        existing = latest_by_measure_region.get(key)
        if existing is None or int(period_text) > int(existing["TIME_PERIOD"]):
            latest_by_measure_region[key] = row

    diagnostics.update({
        "headers": reader.fieldnames or [],
        "row_count": len(rows),
        "territorial_levels": sorted({
            row.get("TERRITORIAL_LEVEL")
            for row in rows
            if row.get("TERRITORIAL_LEVEL")
        }),
        "reference_areas": sorted({
            row.get("REF_AREA")
            for row in rows
            if row.get("REF_AREA")
        }),
        "measure_units": {
            measure: sorted(units)
            for measure, units in sorted(measure_units.items())
        },
        "latest_measure_values": [
            {
                "reference": region,
                "name": row.get("Reference area"),
                "measure": measure,
                "measure_label": row.get("Measure"),
                "unit": row.get("UNIT_MEASURE"),
                "unit_label": row.get("Unit of measure"),
                "time": row.get("TIME_PERIOD"),
                "value": row.get("OBS_VALUE"),
                "country": row.get("COUNTRY"),
            }
            for (measure, region), row in sorted(latest_by_measure_region.items())
        ],
        "ready_for_parser_design": bool(rows),
    })

    print(json.dumps(diagnostics, indent=2, default=str))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
