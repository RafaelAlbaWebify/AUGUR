"""Export dataset-observed Eurostat NUTS2 candidates without changing the database."""
import argparse
import json
from pathlib import Path

from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_geography_discovery import discover_regional_dataset_coverage
from app.ingestion.eurostat_regional_housing import REGIONAL_HOUSING_SERIES
from app.ingestion.eurostat_regional_labour import REGIONAL_LABOUR_SERIES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    adapter = EurostatAdapter(timeout_seconds=120, max_retries=3)
    try:
        report = discover_regional_dataset_coverage(
            adapter, REGIONAL_HOUSING_SERIES + REGIONAL_LABOUR_SERIES)
    finally:
        adapter.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ready": report["ready"],
        "datasets": [{key: item.get(key) for key in
                      ("dataset_id", "status", "country_count", "region_count")}
                     for item in report["datasets"]],
        "file": str(args.output),
    }, indent=2))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
