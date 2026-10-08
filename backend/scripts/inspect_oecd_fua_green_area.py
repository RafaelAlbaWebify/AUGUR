from __future__ import annotations

import csv
import io
import json

import httpx


SOURCE_ID = "OECD"
DATASET_ID = "DSD_FUA_ENV@DF_GREEN_AREA"
DATASET_VERSION = "1.2"
BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_FUA_ENV@DF_GREEN_AREA,1.2"
)
PARAMS = {
    "startPeriod": "2020",
    "dimensionAtObservation": "AllDimensions",
    "format": "csvfilewithlabels",
}
CANDIDATE_KEYS = [
    "AUS01F.A..",
    "AUS01F.A...",
    "AUS01F.A....",
    "AUS01F.A.....",
]


def _rows(text: str) -> tuple[list[str], list[dict]]:
    reader = csv.DictReader(io.StringIO(text))
    return reader.fieldnames or [], list(reader)


def main() -> int:
    attempts = []
    with httpx.Client(
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        selected = None
        headers: list[str] = []
        rows: list[dict] = []

        for key in CANDIDATE_KEYS:
            response = client.get(
                f"{BASE_URL}/{key}",
                params=PARAMS,
            )
            attempt = {
                "key": key,
                "request_url": str(response.request.url),
                "http_status": response.status_code,
                "content_type": response.headers.get("content-type"),
                "response_bytes": len(response.content),
            }
            if response.status_code < 400:
                candidate_headers, candidate_rows = _rows(response.text)
                attempt["row_count"] = len(candidate_rows)
                attempt["headers"] = candidate_headers
                if candidate_rows:
                    selected = key
                    headers = candidate_headers
                    rows = candidate_rows
                    attempts.append(attempt)
                    break
            else:
                attempt["response_preview"] = response.text[:500]
            attempts.append(attempt)

    diagnostics = {
        "source_id": SOURCE_ID,
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "selected_key": selected,
        "attempts": attempts,
        "headers": headers,
        "row_count": len(rows),
        "measures": sorted({
            str(row.get("MEASURE") or "")
            for row in rows
            if row.get("MEASURE")
        }),
        "units": sorted({
            str(row.get("UNIT_MEASURE") or "")
            for row in rows
            if row.get("UNIT_MEASURE")
        }),
        "territorial_levels": sorted({
            str(row.get("TERRITORIAL_LEVEL") or "")
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
            for row in rows[:20]
        ],
        "ready_for_parser_design": bool(rows),
    }
    print(json.dumps(diagnostics, indent=2, default=str))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
