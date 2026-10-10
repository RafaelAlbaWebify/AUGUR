"""Generate a reproducible inventory of defined national indicators.

This inspects repository declarations only; it does NOT claim ingested coverage.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from app.catalog import INDICATORS

FIELDS = ("indicator_id","name","dimension","unit","source_indicator","interpretation_policy","methodology_note","comparability_note")


def inventory() -> dict:
    rows = [{field: indicator.get(field) for field in FIELDS} for indicator in INDICATORS]
    ids = [row["indicator_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate national indicator IDs")
    return {
        "scope": "declared_national_indicators_not_data_availability",
        "indicator_count": len(rows),
        "items": sorted(rows, key=lambda row: (row["dimension"], row["indicator_id"])),
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.suffix.lower() not in (".json", ".csv"):
        p.error("Output must end in .json or .csv")
    result = inventory()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    if a.output.suffix.lower() == ".json":
        a.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        with a.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(result["items"])
    print(json.dumps({"output": str(a.output), "indicator_count": result["indicator_count"],
                      "scope": result["scope"]}))


if __name__ == "__main__":
    main()
