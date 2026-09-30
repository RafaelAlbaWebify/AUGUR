from __future__ import annotations

from collections import defaultdict

from app.db.analytics import future_trajectory


DEFAULT_HORIZONS = [2030, 2035, 2045]


def country_future_trajectory(
    country_iso3: str,
    horizons: list[int] | None = None,
) -> dict:
    selected_horizons = horizons or DEFAULT_HORIZONS
    rows = future_trajectory(country_iso3, selected_horizons)

    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["period"]].append(row)

    horizon_payload = []

    for horizon in selected_horizons:
        indicators = grouped.get(horizon, [])
        sources = sorted({row["source_id"] for row in indicators})

        horizon_payload.append(
            {
                "year": horizon,
                "indicator_count": len(indicators),
                "sources": sources,
                "indicators": indicators,
            }
        )

    return {
        "country_iso3": country_iso3.upper(),
        "method": "official_forecast_horizon_view_v1",
        "horizons": horizon_payload,
        "notes": [
            "This view contains official forecasts/projections only.",
            "It is not an AUGUR prediction or composite score.",
            "Different sources have different forecast horizons.",
        ],
    }
