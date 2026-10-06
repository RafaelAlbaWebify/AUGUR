from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import urljoin
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import httpx


DATASET_PAGE_URL = "https://www.cedefop.europa.eu/en/datasets/stas"
SOURCE_ID = "CEDEFOP"
DATASET_ID = "CEDEFOP_STAS"
DOI = "10.2906/467749508762302"

_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


HEADER_ALIASES = {
    "country": {
        "country",
        "country name",
        "member state",
        "geo",
        "geography",
    },
    "isco": {
        "isco",
        "isco code",
        "isco08",
        "isco 08",
        "occupation code",
        "occupation",
    },
    "year": {
        "year",
        "period",
        "forecast year",
        "reference year",
    },
    "growth_pct": {
        "employment change % growth",
        "employment change growth",
        "employment growth",
        "employment % growth",
        "growth",
        "growth pct",
        "percentage growth",
    },
    "absolute_change": {
        "employment change absolute numbers 000s",
        "employment change absolute",
        "absolute change",
        "employment change 000s",
    },
    "baseline": {
        "baseline",
        "forecast baseline",
        "model baseline",
    },
}


def _normalise_header(value: object) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("%", " % ")
    text = re.sub(r"[_/\\()\[\]{}:;,.\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def resolve_latest_download_url(
    client: httpx.Client,
    dataset_page_url: str = DATASET_PAGE_URL,
) -> str:
    response = client.get(dataset_page_url, follow_redirects=True)
    if response.status_code == 403:
        raise RuntimeError(
            "Cedefop blocks automated access to the STAS dataset page (HTTP 403). "
            "Download the current official XLSX in a browser and rerun the inspector "
            "with --input <path-to-xlsx>. AUGUR does not fall back silently to an older release."
        )
    response.raise_for_status()

    body = html.unescape(response.text)
    candidates = re.findall(
        r"""href=["']([^"']*stas[^"']*\.xlsx(?:\?[^"']*)?)["']""",
        body,
        flags=re.IGNORECASE,
    )
    if not candidates:
        candidates = re.findall(
            r"""href=["']([^"']+\.xlsx(?:\?[^"']*)?)["']""",
            body,
            flags=re.IGNORECASE,
        )

    if not candidates:
        raise RuntimeError(
            "Cedefop STAS dataset page did not expose a downloadable XLSX link."
        )

    # The dataset page should expose the current release first. Prefer paths
    # containing STAS explicitly and keep resolution deterministic.
    candidates = sorted(
        dict.fromkeys(candidates),
        key=lambda value: (
            "stas" not in value.lower(),
            value.lower(),
        ),
    )
    return urljoin(str(response.url), candidates[0])


def download_workbook(
    client: httpx.Client,
    target_path: Path,
    download_url: str | None = None,
) -> dict:
    url = download_url or resolve_latest_download_url(client)
    response = client.get(url, follow_redirects=True)
    response.raise_for_status()

    content_type = (response.headers.get("content-type") or "").lower()
    if "spreadsheet" not in content_type and not url.lower().split("?")[0].endswith(".xlsx"):
        raise RuntimeError(
            f"STAS download did not return an XLSX payload: {content_type or 'unknown content type'}"
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(response.content)

    return {
        "url": str(response.url),
        "path": str(target_path),
        "bytes": len(response.content),
        "content_type": content_type,
    }


def _column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref.upper())
    if not match:
        return 0
    value = 0
    for character in match.group(1):
        value = value * 26 + (ord(character) - ord("A") + 1)
    return value - 1


def _shared_strings(archive: ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in archive.namelist():
        return []

    root = ET.fromstring(archive.read(name))
    values: list[str] = []
    for item in root.findall(f"{{{_MAIN_NS}}}si"):
        parts = [
            node.text or ""
            for node in item.iter(f"{{{_MAIN_NS}}}t")
        ]
        values.append("".join(parts))
    return values


def _sheet_targets(archive: ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))

    target_by_id = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall(f"{{{_PKG_REL_NS}}}Relationship")
    }

    sheets = []
    for sheet in workbook.findall(f".//{{{_MAIN_NS}}}sheet"):
        rel_id = sheet.attrib.get(f"{{{_REL_NS}}}id")
        target = target_by_id.get(rel_id or "")
        if not target:
            continue
        if target.startswith("/"):
            path = target.lstrip("/")
        elif target.startswith("xl/"):
            path = target
        else:
            path = f"xl/{target}"
        sheets.append((sheet.attrib.get("name", path), path))
    return sheets


def _read_sheet_rows(
    archive: ZipFile,
    sheet_path: str,
    shared_strings: list[str],
    max_rows: int = 40,
) -> list[list[object]]:
    root = ET.fromstring(archive.read(sheet_path))
    output: list[list[object]] = []

    for row in root.findall(f".//{{{_MAIN_NS}}}row"):
        cells: dict[int, object] = {}
        for cell in row.findall(f"{{{_MAIN_NS}}}c"):
            ref = cell.attrib.get("r", "A1")
            index = _column_index(ref)
            cell_type = cell.attrib.get("t")
            value_node = cell.find(f"{{{_MAIN_NS}}}v")

            if cell_type == "inlineStr":
                inline = cell.find(f"{{{_MAIN_NS}}}is")
                value = "".join(
                    node.text or ""
                    for node in (inline.iter(f"{{{_MAIN_NS}}}t") if inline is not None else [])
                )
            elif value_node is None:
                value = None
            else:
                raw = value_node.text or ""
                if cell_type == "s":
                    try:
                        value = shared_strings[int(raw)]
                    except (ValueError, IndexError):
                        value = raw
                elif cell_type == "b":
                    value = raw == "1"
                elif cell_type in {"str", "e"}:
                    value = raw
                else:
                    try:
                        number = float(raw)
                        value = int(number) if number.is_integer() else number
                    except ValueError:
                        value = raw

            cells[index] = value

        if cells:
            width = max(cells) + 1
            output.append([cells.get(index) for index in range(width)])
        else:
            output.append([])

        if len(output) >= max_rows:
            break

    return output


def workbook_preview(path: Path, max_rows: int = 40) -> list[dict]:
    with ZipFile(path) as archive:
        shared = _shared_strings(archive)
        sheets = _sheet_targets(archive)
        return [
            {
                "sheet": name,
                "rows": _read_sheet_rows(
                    archive,
                    sheet_path,
                    shared,
                    max_rows=max_rows,
                ),
            }
            for name, sheet_path in sheets
        ]


def detect_table_schema(rows: list[list[object]]) -> dict:
    best: dict | None = None

    for row_index, row in enumerate(rows):
        normalised = [_normalise_header(value) for value in row]
        matches: dict[str, int] = {}

        for field, aliases in HEADER_ALIASES.items():
            for index, header in enumerate(normalised):
                if not header:
                    continue
                if header in aliases or any(
                    alias in header
                    for alias in aliases
                    if len(alias) >= 8
                ):
                    matches[field] = index
                    break

        score = len(matches)
        candidate = {
            "header_row_index": row_index,
            "headers": [str(value or "") for value in row],
            "matches": matches,
            "score": score,
            "core_fields_present": all(
                field in matches
                for field in ("country", "isco", "year")
            ),
            "metric_present": any(
                field in matches
                for field in ("growth_pct", "absolute_change")
            ),
        }

        if best is None or candidate["score"] > best["score"]:
            best = candidate

    if best is None:
        return {
            "status": "no_rows",
            "header_row_index": None,
            "headers": [],
            "matches": {},
            "score": 0,
            "core_fields_present": False,
            "metric_present": False,
        }

    if best["core_fields_present"] and best["metric_present"]:
        best["status"] = "recognised"
    elif best["score"] >= 2:
        best["status"] = "partial"
    else:
        best["status"] = "unrecognised"
    return best


def inspect_workbook(path: Path, max_rows: int = 40) -> dict:
    sheets = workbook_preview(path, max_rows=max_rows)
    diagnostics = []

    for sheet in sheets:
        schema = detect_table_schema(sheet["rows"])
        diagnostics.append(
            {
                "sheet": sheet["sheet"],
                **schema,
                "sample_rows": sheet["rows"][
                    schema["header_row_index"] : schema["header_row_index"] + 4
                ]
                if schema["header_row_index"] is not None
                else sheet["rows"][:4],
            }
        )

    recognised = [
        item for item in diagnostics
        if item["status"] == "recognised"
    ]

    return {
        "dataset_id": DATASET_ID,
        "source_id": SOURCE_ID,
        "doi": DOI,
        "workbook": str(path),
        "sheet_count": len(diagnostics),
        "recognised_sheet_count": len(recognised),
        "ready_for_parser_implementation": bool(recognised),
        "sheets": diagnostics,
        "notes": [
            "This inspector does not write STAS data to DuckDB.",
            "AUGUR only enables ingestion after country, ISCO, year and an employment-change metric are mapped unambiguously.",
        ],
    }
