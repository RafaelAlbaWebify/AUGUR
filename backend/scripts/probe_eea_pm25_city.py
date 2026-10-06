from __future__ import annotations

import argparse
import json

from app.ingestion.eea_air_quality_api import probe_verified_pm25_city


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe verified EEA PM2.5 availability for one city."
    )
    parser.add_argument("--city", default="Oviedo")
    parser.add_argument("--country", default="ES")
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()

    result = probe_verified_pm25_city(
        city_name=args.city,
        country_code=args.country,
        year=args.year,
    )
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["status"] == "available" else 2


if __name__ == "__main__":
    raise SystemExit(main())
