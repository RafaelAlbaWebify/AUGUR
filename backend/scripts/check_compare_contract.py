"""Cross-layer structural contract for the existing country comparison.

Checks the response built by backend/app/services/compare.py against required
TypeScript fields in frontend/src/components/ComparePanel.tsx. This is NOT a
complete TS validator: it targets the critical comparison response contract.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TS_FILE = ROOT / "frontend/src/components/ComparePanel.tsx"

FIELDS = {
    "ComparisonCountryValue": ("period", "value", "source_id"),
    "ComparisonIndicator": ("indicator_id", "name", "dimension", "unit", "countries"),
    "ComparisonResponse": ("countries", "indicator_count", "indicators"),
}


def interface_fields(source: str, type_name: str) -> set[str]:
    marker = re.search(r"\btype\s+" + re.escape(type_name) + r"\s*=\s*\{", source)
    if not marker:
        raise ValueError(f"Missing frontend type declaration: {type_name}")
    depth = 1
    position = marker.end()
    start = position
    while depth and position < len(source):
        if source[position] == "{":
            depth += 1
        elif source[position] == "}":
            depth -= 1
        position += 1
    if depth:
        raise ValueError(f"Unbalanced frontend type declaration: {type_name}")
    body = source[start:position-1]
    # Only match top-level keys; nested type properties are not part of this API.
    result = set()
    level = 0
    for line in body.splitlines():
        stripped = line.strip()
        if level == 0:
            match = re.match(r"([A-Za-z_][A-Za-z_0-9]*)\s*[?:]", stripped)
            if match:
                result.add(match.group(1))
        level += line.count("{") - line.count("}")
    return result


def verify_compare_shape(payload: dict, ts_source: str) -> list[str]:
    errors = []
    for name, fields in FIELDS.items():
        actual = interface_fields(ts_source, name)
        missing = set(fields) - actual
        if missing:
            errors.append(f"Frontend {name} missing required fields: {sorted(missing)}")
    def require(record: object, fields: tuple[str, ...], location: str) -> None:
        if not isinstance(record, dict):
            errors.append(f"{location} must be an object")
            return
        for key in fields:
            if key not in record:
                errors.append(f"{location}.{key} is missing")
    require(payload, FIELDS["ComparisonResponse"], "response")
    if not isinstance(payload, dict):
        return errors
    if not isinstance(payload.get("indicators"), list) or not payload["indicators"]:
        errors.append("response.indicators must contain a fixture indicator")
        return errors
    for index, item in enumerate(payload["indicators"]):
        require(item, FIELDS["ComparisonIndicator"], f"indicators[{index}]")
        if not isinstance(item, dict):
            continue
        countries = item.get("countries")
        if not isinstance(countries, dict) or not countries:
            errors.append(f"indicators[{index}].countries must contain at least one country")
            continue
        for iso3, value in countries.items():
            require(value, FIELDS["ComparisonCountryValue"], f"indicators[{index}].countries[{iso3}]")
    return errors


def fixture_response() -> dict:
    from app.services.compare import build_comparison
    base = dict(indicator_id="unemployment_rate", name="Unemployment",
                dimension="productive_capacity", unit="percent", period=2025,
                value=10.4, source_id="EUROSTAT")
    return build_comparison(["ESP", "IRL"], {
        "ESP": [base],
        "IRL": [dict(base, value=4.7)],
    }, country_names={"ESP": "Spain", "IRL": "Ireland"})


def main() -> None:
    issues = verify_compare_shape(fixture_response(), TS_FILE.read_text(encoding="utf-8"))
    if issues:
        raise SystemExit("Comparison frontend/backend contract failed:\n" + "\n".join(issues))
    print("Comparison frontend/backend structural contract: PASS (synthetic fixture)")


if __name__ == "__main__":
    main()
