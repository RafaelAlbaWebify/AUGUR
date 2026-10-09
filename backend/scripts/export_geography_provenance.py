"""Export stored geography codes and source provenance without changing evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from app.services.geography_provenance import geography_provenance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--country", default=None)
    args = parser.parse_args()
    result = geography_provenance(args.country)
    if args.output.suffix.lower() != ".json":
        parser.error("Provenance export requires .json")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output),
                      "registered_geography_count": result["registered_geography_count"]}, indent=2))


if __name__ == "__main__":
    main()
