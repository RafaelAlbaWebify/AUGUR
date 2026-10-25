"""Strict historical IMF WEO CSV reader: publication must be April 2026.

Never infer vintage from filename or portal URL. Each selected series' own
PUBLICATION_DATE must establish the required archive release.
"""
from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path

EXPECTED = {"real_gdp_growth": ("NGDP_RPCH", "constant prices, percent change"),
            "imf_inflation_average": ("PCPIPCH", "period average, percent change"),
            "imf_unemployment_rate": ("LUR", "unemployment rate")}


def verify_csv(rows: list[dict], file: Path) -> list[dict]:
    selected = [r for r in rows if r["source_id"] == "IMF"]
    expected_keys = {(country, indicator) for country in ("ESP", "IRL") for indicator in EXPECTED}
    if len(selected) != 6 or {(r["country_iso3"], r["indicator_id"]) for r in selected} != expected_keys:
        raise ValueError("Expected exactly six IMF country-indicator rows")
    with file.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        needed = {"SERIES_CODE", "DATASET", "PUBLICATION_DATE", "INDICATOR", "UNIT", "2025"}
        if not needed <= set(reader.fieldnames or []):
            raise ValueError("Missing IMF WEO CSV identity, vintage or values")
        lookup = {}
        for item in reader:
            code = item.get("SERIES_CODE", "")
            parts = code.split(".")
            if len(parts) != 3 or parts[0] not in {"ESP", "IRL"} or parts[2] != "A":
                continue
            if parts[1] not in {v[0] for v in EXPECTED.values()}:
                continue
            if item.get("OBS_MEASURE", "OBS_VALUE") != "OBS_VALUE":
                continue
            key = (parts[0], parts[1])
            if key in lookup:
                raise ValueError(f"Duplicate IMF CSV series: {key}")
            lookup[key] = item
    results = []
    for stored in selected:
        country = stored["country_iso3"]
        indicator = stored["indicator_id"]
        code, semantic = EXPECTED[indicator]
        base = {"country": country, "indicator_id": indicator, "provider": "IMF",
                "period": stored["period"], "stored_value": stored["value"],
                "stored_dataset": stored["dataset_id"], "archive_indicator": code}
        if stored["period"] != 2025 or stored["dataset_id"] != "WEO_APRIL_2026" or stored["unit"] != "percent":
            results.append({**base, "status": "source_drift"});continue
        item = lookup.get((country, code))
        if not item:
            results.append({**base, "status": "missing_or_ambiguous"});continue
        publication = item.get("PUBLICATION_DATE", "")
        if not publication.startswith("2026-04-"):
            results.append({**base, "status": "vintage_unverifiable",
                            "reason": "Downloaded CSV is not the April 2026 historical WEO edition",
                            "archive_publication_date": publication});continue
        description = item.get("INDICATOR", "").casefold()
        unit = item.get("UNIT", "").casefold()
        if (not all(term in description for term in semantic.split(", ")) or
                (code != "LUR" and "percent" not in unit) or
                (code == "LUR" and "unemployment rate" not in description)):
            results.append({**base, "status": "unit_unverifiable",
                            "archive_units": item.get("UNIT"), "archive_description": item.get("INDICATOR")});continue
        try:
            raw = float(item["2025"].replace(",", ""))
        except (ValueError, AttributeError):
            results.append({**base, "status": "missing_or_ambiguous"});continue
        difference = abs(raw-float(stored["value"]))
        tolerance = 0.050000001
        results.append({**base, "status": "match" if difference <= tolerance else "value_drift",
                        "archive_value": raw, "difference": difference,
                        "tolerance": tolerance, "archive_publication_date": publication,
                        "archive_units": item.get("UNIT")})
    return results
