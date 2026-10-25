"""Verify six WEO April 2026 observations against the fixed official XLSX.

The file is supplied by the operator. No network, DB write, or guessed vintage.
Uses only stdlib ZIP/XML, supporting shared and inline strings.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "p": "http://schemas.openxmlformats.org/package/2006/relationships"}
TARGET_CODES = {"real_gdp_growth": ("NGDP_RPCH", "percent"),
                "imf_inflation_average": ("PCPIPCH", "percent"),
                "imf_unemployment_rate": ("LUR", "percent")}
EXPECTED_COUNTRIES = {"ESP", "IRL"}


def _col(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref)
    n = 0
    for letter in letters.group(0):
        n = 26 * n + ord(letter) - 64
    return n - 1


def _read_rows(z: zipfile.ZipFile, sheet_name: str = "Countries") -> list[list[str]]:
    main = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    targets = {x.attrib["Id"]: x.attrib["Target"] for x in rels}
    sheets = main.find("m:sheets", NS)
    sheet = next((x for x in sheets if x.attrib.get("name", "").casefold() == sheet_name.casefold()), None)
    if sheet is None:
        raise ValueError("Official workbook has no Countries sheet")
    rid = sheet.attrib[f'{{{NS["r"]}}}id']
    target = targets[rid].lstrip("/")
    if not target.startswith("xl/"):
        target = "xl/" + target
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for item in root.findall("m:si", NS):
            shared.append("".join(e.text or "" for e in item.findall(".//m:t", NS)))
    xml = ET.fromstring(z.read(target))
    rows = []
    for row in xml.findall(".//m:sheetData/m:row", NS):
        cells = {}
        for cell in row.findall("m:c", NS):
            idx = _col(cell.attrib["r"])
            element = cell.find("m:v", NS)
            if cell.attrib.get("t") == "inlineStr":
                value = "".join(x.text or "" for x in cell.findall(".//m:t", NS))
            else:
                value = "" if element is None else element.text or ""
            if cell.attrib.get("t") == "s" and value:
                value = shared[int(value)]
            cells[idx] = value
        if cells:
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
    return rows


def _norm(v: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(v).casefold())


def extract_cells(path: Path) -> dict[tuple[str, str], dict]:
    """Fail closed if country/code/period/units cannot be uniquely identified."""
    with zipfile.ZipFile(path) as z:
        records = _read_rows(z)
    keys = {"country": {"iso", "iso3", "isocode", "countryiso3", "countrycode"},
            "indicator": {"weosubjectcode", "subjectdescriptorcode", "weocode", "indicatorcode"},
            "unit": {"units", "unit"},
            "year": {"2025"}}
    head_idx = None
    mapping = {}
    for i, cells in enumerate(records[:30]):
        normalized = [_norm(x) for x in cells]
        candidates = {key: next((j for j, h in enumerate(normalized) if h in options), None)
                      for key, options in keys.items()}
        if all(v is not None for v in candidates.values()):
            head_idx, mapping = i, candidates
            break
    if head_idx is None:
        raise ValueError("Cannot identify ISO, WEO subject code, Units and 2025 columns; archive schema not certified")
    result = {}
    for cells in records[head_idx + 1:]:
        def get(name):
            i = mapping[name]
            return str(cells[i]).strip() if i < len(cells) else ""
        country = get("country").upper()
        code = get("indicator").upper()
        if country not in EXPECTED_COUNTRIES or code not in {x[0] for x in TARGET_CODES.values()}:
            continue
        units = get("unit")
        raw = get("year").replace(",", "").strip()
        if raw in {"", "n/a", "NA", ".."}:
            continue
        value = float(raw)
        key = (country, code)
        if key in result:
            raise ValueError(f"Duplicate IMF archive observation {key}")
        result[key] = {"value": value, "units": units}
    return result


def compare_weo_archive(rows: list[dict], archive: Path) -> list[dict]:
    if archive.suffix.lower() == '.csv':
        from scripts.verify_imf_weo_csv import verify_csv
        return verify_csv(rows, archive)
    selected = [r for r in rows if r["source_id"] == "IMF"]
    if len(selected) != 6 or {(r["country_iso3"], r["indicator_id"]) for r in selected} != {
        (country, ind) for country in EXPECTED_COUNTRIES for ind in TARGET_CODES
    }:
        raise ValueError("Expected exactly six Spain/Ireland IMF observations")
    cells = extract_cells(archive)
    output = []
    for r in selected:
        code, unit = TARGET_CODES[r["indicator_id"]]
        base = {"country": r["country_iso3"], "indicator_id": r["indicator_id"],
                "provider": "IMF", "period": r["period"], "stored_value": r["value"],
                "stored_dataset": r["dataset_id"], "archive_indicator": code}
        if r["dataset_id"] != "WEO_APRIL_2026" or r["unit"] != unit or r["period"] != 2025:
            output.append({**base, "status": "source_drift"});continue
        item = cells.get((r["country_iso3"], code))
        if not item:
            output.append({**base, "status": "missing_or_ambiguous"});continue
        unit_text = item["units"].casefold()
        expected_units = ("percent" in unit_text and ("change" in unit_text if code != "LUR" else True))
        if not expected_units:
            output.append({**base, "status": "unit_unverifiable", "archive_units": item["units"]});continue
        delta = abs(item["value"] - float(r["value"]))
        tolerance = 0.050000001  # persisted IMF WEO observations are shown at 1 decimal
        output.append({**base, "status": "match" if delta <= tolerance else "value_drift",
                       "archive_value": item["value"], "difference": delta,
                       "tolerance": tolerance, "archive_units": item["units"]})
    return output
