from __future__ import annotations

import json

from app.ingestion.eea_air_quality_api import inspect_modern_eea_api


def main() -> int:
    result = inspect_modern_eea_api()
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["ready_for_endpoint_design"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
