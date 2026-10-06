from __future__ import annotations

import argparse
import json

from app.ingestion.eea_city_air import fetch_city_pm25_annual


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="Oviedo")
    parser.add_argument("--country", default="ES")
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()

    result = fetch_city_pm25_annual(
        args.city,
        args.country,
        args.year,
    )
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") == "available" else 2


if __name__ == "__main__":
    raise SystemExit(main())
