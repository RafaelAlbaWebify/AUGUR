from __future__ import annotations

from app.catalog import COUNTRIES
from app.db.bootstrap import initialize_datastores
from app.db.analytics import latest_observations


RADAR_INDICATORS = [
    ("safety", "intentional_homicide_rate"),
    ("environment", "pm25_premature_death_rate"),
    ("infrastructure", "household_internet_access"),
]


def radar_evidence_status() -> tuple[list[dict], bool]:
    initialize_datastores()
    rows: list[dict] = []
    complete = True

    for country in COUNTRIES:
        iso3 = country["iso3"]
        latest = {
            item["indicator_id"]: item
            for item in latest_observations(iso3)
        }

        for domain, indicator_id in RADAR_INDICATORS:
            item = latest.get(indicator_id)
            if item is None:
                complete = False
                rows.append({
                    "country_iso3": iso3,
                    "domain": domain,
                    "indicator_id": indicator_id,
                    "status": "missing",
                })
                continue

            rows.append({
                "country_iso3": iso3,
                "domain": domain,
                "indicator_id": indicator_id,
                "status": "available",
                "period": item["period"],
                "value": item["value"],
                "unit": item["unit"],
                "source_id": item["source_id"],
            })

    return rows, complete


def main() -> int:
    rows, complete = radar_evidence_status()

    print("AUGUR COUNTRY RADAR EVIDENCE CHECK")
    print("=" * 72)

    for row in rows:
        prefix = f"{row['country_iso3']} · {row['domain']:<14}"
        if row["status"] == "missing":
            print(f"{prefix} MISSING · {row['indicator_id']}")
            continue

        print(
            f"{prefix} OK · {row['indicator_id']} · "
            f"{row['value']} {row['unit']} · {row['period']} · {row['source_id']}"
        )

    print("=" * 72)
    print("Complete:", complete)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
