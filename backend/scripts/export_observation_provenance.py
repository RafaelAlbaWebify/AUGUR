"""Export local source, dataset, unit and period evidence as JSON."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from app.services.observation_provenance import observation_provenance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--country")
    args = parser.parse_args()
    if args.output.suffix.lower() != ".json":
        parser.error("Only JSON output is supported")
    result = observation_provenance(args.country)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "groups": result["row_count"],
                      "unregistered_geographies": len(result["unregistered_observations"])}))


if __name__ == "__main__":
    main()
