from __future__ import annotations

import json

from app.ingestion.eea_health_burden import inspect_eea_pm25_burden_dataset


def main() -> int:
    result = inspect_eea_pm25_burden_dataset()
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("ready_for_parser_design") else 2


if __name__ == "__main__":
    raise SystemExit(main())
