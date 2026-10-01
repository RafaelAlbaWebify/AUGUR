from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioValue:
    baseline: float
    improvement: float
    stress: float
    assumption: str
    uncertainty_multiplier: float
    uncertainty_level: str


def horizon_uncertainty(year: int) -> tuple[float, str]:
    if year <= 2030:
        return 1.0, "near"
    if year <= 2035:
        return 1.5, "medium"
    return 2.5, "long"


def build_scenario_value(
    indicator_id: str,
    baseline: float,
    year: int,
    target_min: float | None = None,
    target_max: float | None = None,
) -> ScenarioValue:
    value = float(baseline)
    multiplier, level = horizon_uncertainty(year)

    if indicator_id == "real_gdp_growth":
        return ScenarioValue(
            baseline=value,
            improvement=value + (0.5 * multiplier),
            stress=value - (0.75 * multiplier),
            assumption=(
                "AUGUR model assumption: base envelope is +0.5pp / -0.75pp "
                "versus the official forecast, widened by horizon uncertainty."
            ),
            uncertainty_multiplier=multiplier,
            uncertainty_level=level,
        )

    if indicator_id == "imf_unemployment_rate":
        return ScenarioValue(
            baseline=value,
            improvement=max(0.0, value - (1.0 * multiplier)),
            stress=value + (1.5 * multiplier),
            assumption=(
                "AUGUR model assumption: base envelope is -1.0pp / +1.5pp "
                "versus the official forecast, widened by horizon uncertainty."
            ),
            uncertainty_multiplier=multiplier,
            uncertainty_level=level,
        )

    if indicator_id == "imf_inflation_average":
        midpoint = (
            (target_min + target_max) / 2.0
            if target_min is not None and target_max is not None
            else 2.0
        )
        improvement_step = (midpoint - value) * min(1.0, 0.5 * multiplier)
        improvement = value + improvement_step
        stress = value + (1.5 * multiplier)

        return ScenarioValue(
            baseline=value,
            improvement=improvement,
            stress=stress,
            assumption=(
                "AUGUR model assumption: improvement moves toward the target midpoint; "
                "stress adds a horizon-scaled inflation shock."
            ),
            uncertainty_multiplier=multiplier,
            uncertainty_level=level,
        )

    if indicator_id == "life_expectancy":
        spread = 0.8 * multiplier
        return ScenarioValue(
            baseline=value,
            improvement=value + spread,
            stress=max(0.0, value - spread),
            assumption=(
                "AUGUR model assumption: life-expectancy envelope widens from "
                "+/-0.8 years as the horizon extends."
            ),
            uncertainty_multiplier=multiplier,
            uncertainty_level=level,
        )

    return ScenarioValue(
        baseline=value,
        improvement=value,
        stress=value,
        assumption=(
            "Contextual indicator: no automatic positive/negative adjustment applied. "
            "Horizon uncertainty is reported but does not alter the value."
        ),
        uncertainty_multiplier=multiplier,
        uncertainty_level=level,
    )
