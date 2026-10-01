from __future__ import annotations

from app.catalog import INDICATORS
from app.db.analytics import future_trajectory
from app.engines.scenario import build_scenario_value
from app.services.trajectory import DEFAULT_HORIZONS


def country_scenarios(
    country_iso3: str,
    horizons: list[int] | None = None,
) -> dict:
    selected_horizons = horizons or DEFAULT_HORIZONS
    rows = future_trajectory(country_iso3, selected_horizons)
    catalog = {item["indicator_id"]: item for item in INDICATORS}

    scenario_rows = []

    for row in rows:
        indicator = catalog[row["indicator_id"]]
        scenario = build_scenario_value(
            row["indicator_id"],
            row["value"],
            indicator.get("target_min"),
            indicator.get("target_max"),
        )

        scenario_rows.append(
            {
                **row,
                "official_baseline": scenario.baseline,
                "scenarios": {
                    "baseline": scenario.baseline,
                    "improvement": scenario.improvement,
                    "stress": scenario.stress,
                },
                "assumption": scenario.assumption,
            }
        )

    return {
        "country_iso3": country_iso3.upper(),
        "method": "augur_scenario_envelope_v1",
        "horizons": selected_horizons,
        "scenario_names": ["baseline", "improvement", "stress"],
        "indicators": scenario_rows,
        "notes": [
            "Baseline equals the official forecast/projection.",
            "Improvement and stress are AUGUR model assumptions, not official forecasts.",
            "Contextual indicators are not directionally adjusted in v1.",
            "No composite score is produced.",
        ],
    }
