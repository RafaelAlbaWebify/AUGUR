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
RELEASE_VERSION = "2026"
TARGET_SHEET_COUNTRIES = {
    "ES": "ESP",
    "PT": "PRT",
    "IE": "IRL",
}

ISCO08_SUBMAJOR_BY_LABEL = {
    "commissioned armed forces officers": "01",
    "non commissioned armed forces officers": "02",
    "armed forces occupations other ranks": "03",
    "chief executives senior officials and legislators": "11",
    "administrative and commercial managers": "12",
    "production and specialised services managers": "13",
    "production and specialized services managers": "13",
    "hospitality retail and other services managers": "14",
    "science and engineering professionals": "21",
    "health professionals": "22",
    "teaching professionals": "23",
    "business and administration professionals": "24",
    "information and communications technology professionals": "25",
    "legal social and cultural professionals": "26",
    "science and engineering associate professionals": "31",
    "health associate professionals": "32",
    "business and administration associate professionals": "33",
    "legal social cultural and related associate professionals": "34",
    "information and communications technicians": "35",
    "general and keyboard clerks": "41",
    "customer services clerks": "42",
    "numerical and material recording clerks": "43",
    "other clerical support workers": "44",
    "personal service workers": "51",
    "sales workers": "52",
    "personal care workers": "53",
    "protective services workers": "54",
    "market oriented skilled agricultural workers": "61",
    "market oriented skilled forestry fishery and hunting workers": "62",
    "subsistence farmers fishers hunters and gatherers": "63",
    "building and related trades workers excluding electricians": "71",
    "metal machinery and related trades workers": "72",
    "handicraft and printing workers": "73",
    "electrical and electronic trades workers": "74",
    "food processing wood working garment and other craft and related trades workers": "75",
    "stationary plant and machine operators": "81",
    "assemblers": "82",
    "drivers and mobile plant operators": "83",
    "cleaners and helpers": "91",
    "agricultural forestry and fishery labourers": "92",
    "labourers in mining construction manufacturing and transport": "93",
    "food preparation assistants": "94",
    "street and related sales and service workers": "95",
    "refuse workers and other elementary workers": "96",
}


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
        "occupation group 2 digit",
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
        "labour shortage index",
        "labour shortage indexx",
        "index",
    },
    "year": {
        "year",
        "period",
        "forecast year",
        "reference year",
    },
    "lsi_comp": {"lsi comp"},
    "lsi1": {"lsi1"},
    "lsi2": {"lsi2"},
    "lsi3": {"lsi3"},
}


def _normalise_header(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[_/\\()\[\]{}:;,\.\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalise_occupation_label(value: object) -> str:
    return _normalise_header(value)


def resolve_isco2_label(value: object) -> str | None:
    return ISCO08_SUBMAJOR_BY_LABEL.get(
        _normalise_occupation_label(value)
    )


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
    *,
    sheet_name: str | None = None,
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
            or (
                sheet_name is not None
                and (
                    sheet_name in TARGET_SHEET_COUNTRIES
                    or sheet_name == "EU27"
                    or re.fullmatch(r"[A-Z]{2}", sheet_name) is not None
                )
            )
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
            "country_from_sheet": (
                sheet_name
                if sheet_name and "country" not in matches and "country_code" not in matches
                else None
            ),
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
            sheet_name=sheet["sheet"],
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
