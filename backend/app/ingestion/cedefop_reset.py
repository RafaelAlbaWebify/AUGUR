from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import urljoin

import httpx

from app.ingestion.cedefop_clssi import workbook_preview


SOURCE_ID = "CEDEFOP"
DATASET_ID = "CEDEFOP_RESET"
DATASET_PAGE_URL = (
    "https://www.cedefop.europa.eu/en/datasets/"
    "regional-skills-ecosystem-index"
)
DOI = "10.2906/861717916754276"
RELEASE_VERSION = "2026-10"
REFERENCE_YEAR = 2024


def resolve_download_url(
    client: httpx.Client,
    dataset_page_url: str = DATASET_PAGE_URL,
) -> dict:
    response = client.get(dataset_page_url, follow_redirects=True)

    if response.status_code == 403:
        return {
            "status": "access_blocked",
            "status_code": 403,
            "dataset_page_url": dataset_page_url,
            "download_url": None,
        }

    response.raise_for_status()
    body = html.unescape(response.text)

    candidates = re.findall(
        r"""href=["']([^"']+\.xlsx(?:\?[^"']*)?)["']""",
        body,
        flags=re.IGNORECASE,
    )
    candidates = list(dict.fromkeys(candidates))

    if not candidates:
        return {
            "status": "download_link_not_found",
            "status_code": response.status_code,
            "dataset_page_url": str(response.url),
            "download_url": None,
        }

    reset_candidates = [
        value
        for value in candidates
        if any(
            token in value.lower()
            for token in ("reset", "regional", "skill")
        )
    ]
    selected = (reset_candidates or candidates)[0]

    return {
        "status": "available",
        "status_code": response.status_code,
        "dataset_page_url": str(response.url),
        "download_url": urljoin(str(response.url), selected),
        "candidate_count": len(candidates),
    }


def download_workbook(
    client: httpx.Client,
    target_path: Path,
    download_url: str,
) -> dict:
    response = client.get(download_url, follow_redirects=True)
    response.raise_for_status()

    content_type = (
        response.headers.get("content-type") or ""
    ).lower()
    if (
        "spreadsheet" not in content_type
        and not str(response.url).lower().split("?")[0].endswith(".xlsx")
    ):
        raise RuntimeError(
            "RESET download did not return an XLSX payload: "
            f"{content_type or 'unknown content type'}"
        )

    if not response.content:
        raise RuntimeError("RESET workbook download is empty.")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(response.content)

    return {
        "url": str(response.url),
        "path": str(target_path),
        "bytes": len(response.content),
        "content_type": content_type,
    }


def inspect_workbook(path: Path, max_rows: int = 12) -> dict:
    sheets = workbook_preview(path, max_rows=max_rows)
    return {
        "status": "available",
        "dataset_id": DATASET_ID,
        "source_id": SOURCE_ID,
        "release_version": RELEASE_VERSION,
        "reference_year": REFERENCE_YEAR,
        "doi": DOI,
        "workbook": str(path),
        "sheet_count": len(sheets),
        "sheets": [
            {
                "sheet": sheet["sheet"],
                "row_count_previewed": len(sheet["rows"]),
                "sample_rows": sheet["rows"][:6],
            }
            for sheet in sheets
        ],
        "notes": [
            "This inspector never writes RESET data to DuckDB.",
            "RESET is NUTS2 regional skills-ecosystem evidence and must remain separate from occupation-specific vacancy/shortage evidence.",
            "AUGUR will only design a parser after inspecting the official workbook schema.",
        ],
    }
