from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioValue:
    baseline: float
    improvement: float
    stress: float
    assumption: str


def build_scenario_value(
    indicator_id: str,
    baseline: float,
    target_min: float | None = None,
    target_max: float | None = None,
) -> ScenarioValue:
    value = float(baseline)

    if indicator_id == "real_gdp_growth":
        return ScenarioValue(
            baseline=value,
            improvement=value + 0.5,
            stress=value - 0.75,
            assumption="AUGUR model assumption: +0.5pp improvement / -0.75pp stress versus official forecast.",
        )

    if indicator_id == "imf_unemployment_rate":
        return ScenarioValue(
            baseline=value,
            improvement=max(0.0, value - 1.0),
            stress=value + 1.5,
            assumption="AUGUR model assumption: -1.0pp improvement / +1.5pp stress versus official forecast.",
        )

    if indicator_id == "imf_inflation_average":
        midpoint = (
            (target_min + target_max) / 2.0
            if target_min is not None and target_max is not None
            else 2.0
        )
        improvement = value + (midpoint - value) * 0.5
        stress = value + 1.5
        return ScenarioValue(
            baseline=value,
            improvement=improvement,
            stress=stress,
            assumption="AUGUR model assumption: improvement moves halfway toward target midpoint; stress adds 1.5pp.",
        )

    if indicator_id == "life_expectancy":
        return ScenarioValue(
            baseline=value,
            improvement=value + 0.8,
            stress=max(0.0, value - 0.8),
            assumption="AUGUR model assumption: +/-0.8 years around the official UN projection.",
        )

    return ScenarioValue(
        baseline=value,
        improvement=value,
        stress=value,
        assumption="Contextual indicator: no automatic positive/negative adjustment applied.",
    )
