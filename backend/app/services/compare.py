from __future__ import annotations

from app.db.analytics import latest_observations
from app.services.country import country_metadata


def build_comparison(
    country_iso3s: list[str],
    snapshots: dict[str, list[dict]],
    country_names: dict[str, str] | None = None,
) -> dict:
    indicator_rows: dict[str, dict] = {}

    for country_iso3 in country_iso3s:
        for item in snapshots.get(country_iso3, []):
            row = indicator_rows.setdefault(
                item["indicator_id"],
                {
                    "indicator_id": item["indicator_id"],
                    "name": item["name"],
                    "dimension": item["dimension"],
                    "unit": item["unit"],
                    "countries": {},
                },
            )

            row["countries"][country_iso3] = {
                "period": item["period"],
                "value": item["value"],
                "source_id": item["source_id"],
            }

    names = country_names or {}
    countries = [
        {
            "iso3": code,
            "name": names.get(code, code),
        }
        for code in country_iso3s
    ]

    rows = sorted(
        indicator_rows.values(),
        key=lambda item: (item["dimension"], item["name"]),
    )

    return {
        "countries": countries,
        "indicator_count": len(rows),
        "indicators": rows,
        "method": "aligned_current_observations_v1",
        "notes": [
            "No composite score or ranking is produced.",
            "Periods may differ where source publication schedules differ.",
            "Each value retains its preferred source identifier.",
        ],
    }


def country_comparison(country_iso3s: list[str]) -> dict:
    normalized = [code.upper() for code in country_iso3s]
    snapshots = {
        code: latest_observations(code)
        for code in normalized
    }
    country_names = {
        code: country_metadata(code)["name"]
        for code in normalized
    }
    return build_comparison(
        normalized,
        snapshots,
        country_names=country_names,
    )
