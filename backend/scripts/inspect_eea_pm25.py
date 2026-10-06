from __future__ import annotations

import json

from app.ingestion.eea_air_quality import inspect_eea_pm25


def main() -> int:
    result = inspect_eea_pm25()
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["ready_for_aggregation_design"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
