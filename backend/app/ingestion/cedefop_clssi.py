from __future__ import annotations

import re
from pathlib import Path

import httpx

from app.ingestion.cedefop_stas import workbook_preview


SOURCE_ID = "CEDEFOP"
DATASET_ID = "CEDEFOP_CLSSI"
DATASET_PAGE_URL = (
    "https://www.cedefop.europa.eu/en/datasets/labour-skills-shortage-index"
)
DOWNLOAD_URL = (
    "https://www.cedefop.europa.eu/files/"
    "2026_cedefop_labour_skills_shortage_index_clssi_dataset.xlsx"
)
DOWNLOAD_LABEL = "2026 Cedefop Labour Skills Shortage Index (CLSSI) dataset"
CATALOG_VERSION = "2024"


HEADER_ALIASES = {
    "country": {
        "country",
        "country name",
        "member state",
        "geo",
        "geography",
    },
    "country_code": {
        "country code",
        "country_code",
        "geo code",
        "geo_code",
    },
    "occupation": {
        "occupation",
        "occupation name",
        "occupation label",
        "isco occupation",
    },
    "isco": {
        "isco",
        "isco code",
        "isco08",
        "isco 08",
        "isco-08",
        "occupation code",
    },
    "index": {
        "clssi",
        "clssi index",
        "shortage index",
        "labour skills shortage index",
        "labour and skills shortage index",
        "index",
    },
    "year": {
        "year",
        "period",
        "forecast year",
        "reference year",
    },
}


def _normalise_header(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[_/\\()\[\]{}:;,\.\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def download_workbook(
    target_path: Path,
    *,
    url: str = DOWNLOAD_URL,
    client: httpx.Client | None = None,
) -> dict:
    owns_client = client is None
    client = client or httpx.Client(
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    )
    try:
        response = client.get(url)
        response.raise_for_status()
        content_type = (
            response.headers.get("content-type")
            or ""
        ).lower()
        if (
            "spreadsheet" not in content_type
            and not str(response.url).lower().split("?")[0].endswith(".xlsx")
            and not response.content.startswith(b"PK")
        ):
            raise RuntimeError(
                "CLSSI download did not return an XLSX payload: "
                + (content_type or "unknown content type")
            )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(response.content)
        return {
            "url": str(response.url),
            "path": str(target_path),
            "bytes": len(response.content),
            "content_type": content_type,
        }
    finally:
        if owns_client:
            client.close()


def detect_sheet_schema(
    rows: list[list[object]],
) -> dict:
    best = None

    for row_index, row in enumerate(rows):
        headers = [_normalise_header(value) for value in row]
        matches: dict[str, int] = {}

        for field, aliases in HEADER_ALIASES.items():
            for index, header in enumerate(headers):
                if header in aliases:
                    matches[field] = index
                    break

        year_columns = {
            int(str(value).strip()): index
            for index, value in enumerate(row)
            if re.fullmatch(r"20\d{2}", str(value or "").strip())
        }

        has_country = (
            "country" in matches
            or "country_code" in matches
        )
        has_occupation = (
            "occupation" in matches
            or "isco" in matches
        )
        shortage_like = any(
            "shortage" in header
            or "clssi" in header
            for header in headers
            if header
        )
        score = (
            2 * int(has_country)
            + 2 * int(has_occupation)
            + 2 * int("index" in matches)
            + int("year" in matches)
            + 2 * int(bool(year_columns))
            + int(shortage_like)
            + len(matches)
        )

        candidate = {
            "header_row_index": row_index,
            "headers": [
                str(value or "")
                for value in row
            ],
            "matches": matches,
            "year_columns": year_columns,
            "shortage_like_headers": [
                str(row[index] or "")
                for index, header in enumerate(headers)
                if "shortage" in header or "clssi" in header
            ],
            "score": score,
            "has_country": has_country,
            "has_occupation": has_occupation,
        }

        if best is None or score > best["score"]:
            best = candidate

    if best is None:
        return {
            "status": "no_rows",
            "header_row_index": None,
            "headers": [],
            "matches": {},
            "year_columns": {},
            "shortage_like_headers": [],
            "score": 0,
            "has_country": False,
            "has_occupation": False,
        }

    if (
        best["has_country"]
        and best["has_occupation"]
        and (
            "index" in best["matches"]
            or best["shortage_like_headers"]
            or best["year_columns"]
        )
    ):
        best["status"] = "candidate"
    elif best["score"] >= 4:
        best["status"] = "partial"
    else:
        best["status"] = "unrecognised"

    return best


def inspect_workbook(
    path: Path,
    *,
    max_rows: int = 80,
) -> dict:
    sheets = workbook_preview(
        path,
        max_rows=max_rows,
    )
    diagnostics = []

    for sheet in sheets:
        schema = detect_sheet_schema(
            sheet["rows"],
        )
        header_index = schema["header_row_index"]
        diagnostics.append({
            "sheet": sheet["sheet"],
            **schema,
            "sample_rows": (
                sheet["rows"][
                    header_index : header_index + 5
                ]
                if header_index is not None
                else sheet["rows"][:5]
            ),
        })

    candidates = [
        item
        for item in diagnostics
        if item["status"] == "candidate"
    ]

    return {
        "dataset_id": DATASET_ID,
        "source_id": SOURCE_ID,
        "dataset_page_url": DATASET_PAGE_URL,
        "download_url": DOWNLOAD_URL,
        "download_label": DOWNLOAD_LABEL,
        "catalog_version": CATALOG_VERSION,
        "workbook": str(path),
        "sheet_count": len(diagnostics),
        "candidate_sheet_count": len(candidates),
        "ready_for_parser_implementation": bool(candidates),
        "sheets": diagnostics,
        "notes": [
            "This inspector never writes CLSSI data to DuckDB.",
            "Cedefop currently labels the downloadable file as 2026 while the dataset catalog page still displays Version 2024; AUGUR keeps both facts explicit until workbook metadata/schema are inspected.",
            "AUGUR will not infer CLSSI column meanings before a real workbook inspection.",
        ],
    }
