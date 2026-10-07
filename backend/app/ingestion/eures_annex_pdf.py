from __future__ import annotations

import csv
import re
from pathlib import Path

import httpx
import pdfplumber


DEFAULT_EURES_ANNEX_URL = (
    "https://www.ela.europa.eu/sites/default/files/2026-06/"
    "annex-labour-shortages-report-ela-2025.pdf"
)

COUNTRY_CODE_RE = re.compile(r"\b[A-Z]{2}\b")
HEADER_OCCUPATION = "occupation"
HEADER_SHORTAGE = "countries reporting a shortage"
HEADER_SURPLUS = "countries reporting a surplus"


def _clean_cell(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).replace("\u00ad", "").split())


def _country_codes(value: str | None) -> list[str]:
    text = _clean_cell(value).upper()
    result: list[str] = []
    for code in COUNTRY_CODE_RE.findall(text):
        if code not in result:
            result.append(code)
    return result


def normalize_annex_table(table: list[list[str | None]]) -> list[dict]:
    if not table:
        return []

    header_index = None
    for index, row in enumerate(table):
        cells = [_clean_cell(cell).lower() for cell in row[:3]]
        if len(cells) < 3:
            continue
        if (
            HEADER_OCCUPATION in cells[0]
            and HEADER_SHORTAGE in cells[1]
            and HEADER_SURPLUS in cells[2]
        ):
            header_index = index
            break

    if header_index is None:
        return []

    normalized = []
    for row in table[header_index + 1 :]:
        if len(row) < 3:
            continue

        occupation = _clean_cell(row[0])
        shortages = _country_codes(row[1])
        surpluses = _country_codes(row[2])

        if not occupation:
            continue

        lower = occupation.lower()
        if (
            lower == HEADER_OCCUPATION
            or lower.startswith("eures |")
            or lower.startswith("table 21")
        ):
            continue

        if not shortages and not surpluses:
            continue

        normalized.append({
            "occupation_label": occupation,
            "shortage_countries": " ".join(shortages),
            "surplus_countries": " ".join(surpluses),
        })

    return normalized


def extract_eures_annex_rows_from_pdf(
    path: str | Path,
) -> tuple[list[dict], dict]:
    source_path = Path(path).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    rows: list[dict] = []
    table_count = 0
    pages_with_rows = 0

    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "intersection_tolerance": 5,
        "snap_tolerance": 4,
        "join_tolerance": 4,
    }

    with pdfplumber.open(source_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_rows = []
            for table in page.extract_tables(table_settings=table_settings):
                table_count += 1
                page_rows.extend(normalize_annex_table(table))

            if page_rows:
                pages_with_rows += 1
                rows.extend(page_rows)

        page_count = len(pdf.pages)

    by_occupation: dict[str, dict] = {}
    duplicates = []
    for row in rows:
        key = row["occupation_label"].casefold()
        existing = by_occupation.get(key)
        if existing is None:
            by_occupation[key] = row
            continue

        if (
            existing["shortage_countries"] != row["shortage_countries"]
            or existing["surplus_countries"] != row["surplus_countries"]
        ):
            duplicates.append({
                "occupation_label": row["occupation_label"],
                "first": existing,
                "duplicate": row,
            })

    unique_rows = sorted(
        by_occupation.values(),
        key=lambda item: item["occupation_label"].casefold(),
    )

    diagnostics = {
        "source_path": str(source_path),
        "page_count": page_count,
        "table_count": table_count,
        "pages_with_rows": pages_with_rows,
        "row_count": len(unique_rows),
        "duplicate_conflict_count": len(duplicates),
        "duplicate_conflicts": duplicates,
        "ready_for_esco_review": bool(unique_rows) and not duplicates,
        "parser": "pdfplumber_grid_table_v1",
        "notes": [
            "The extractor uses visible PDF table grid lines rather than OCR.",
            "Occupation labels and country lists remain source text until the separate ESCO/ISCO review step.",
            "Conflicting duplicate occupations block readiness instead of being merged silently.",
        ],
    }

    return unique_rows, diagnostics


def write_normalized_annex_csv(
    rows: list[dict],
    path: str | Path,
) -> Path:
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "occupation_label",
                "shortage_countries",
                "surplus_countries",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return output


def download_eures_annex(
    path: str | Path,
    *,
    url: str = DEFAULT_EURES_ANNEX_URL,
) -> Path:
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "pdf" not in content_type.lower() and not response.content.startswith(b"%PDF"):
            raise ValueError("ELA annex response is not a PDF")
        output.write_bytes(response.content)

    return output
