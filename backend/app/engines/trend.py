from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass
class TrendResult:
    direction: str
    interpretation: str
    confidence: str
    slope_per_year: float | None
    pct_change_1y: float | None
    pct_change_3y: float | None
    pct_change_5y: float | None
    years_used: int
    target_status: str | None


def _pct_change(current: float, previous: float | None) -> float | None:
    if previous is None or previous == 0:
        return None
    return ((current - previous) / abs(previous)) * 100.0


def _linear_slope(points: list[tuple[int, float]]) -> float | None:
    if len(points) < 2:
        return None

    xs = [float(year) for year, _ in points]
    ys = [float(value) for _, value in points]
    x_mean = mean(xs)
    y_mean = mean(ys)

    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return None

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    return numerator / denominator


def _direction_from_change(change: float | None) -> str:
    if change is None:
        return "unknown"
    magnitude = abs(change)
    if magnitude < 1.0:
        return "stable"
    if change > 0:
        return "strong_increase" if magnitude >= 10.0 else "increase"
    return "strong_decrease" if magnitude >= 10.0 else "decrease"


def _distance_to_range(value: float, target_min: float, target_max: float) -> float:
    if target_min <= value <= target_max:
        return 0.0
    if value < target_min:
        return target_min - value
    return value - target_max


def _interpret_directional(direction: str, policy: str) -> str:
    if direction in {"unknown", "stable"}:
        return "neutral_or_contextual"

    increasing = direction in {"increase", "strong_increase"}

    if policy == "higher":
        return "improving" if increasing else "deteriorating"

    if policy == "lower":
        return "deteriorating" if increasing else "improving"

    return "neutral_or_contextual"


def _interpret_target_range(
    current: float,
    reference: float | None,
    target_min: float,
    target_max: float,
) -> tuple[str, str]:
    current_distance = _distance_to_range(current, target_min, target_max)

    if current_distance == 0:
        return "within_target", "within_target"

    target_status = "below_target" if current < target_min else "above_target"

    if reference is None:
        return "neutral_or_contextual", target_status

    previous_distance = _distance_to_range(reference, target_min, target_max)

    if current_distance < previous_distance:
        return "improving", target_status
    if current_distance > previous_distance:
        return "deteriorating", target_status

    return "neutral_or_contextual", target_status


def calculate_trend(
    series: list[tuple[int, float]],
    interpretation_policy: str,
    target_min: float | None = None,
    target_max: float | None = None,
) -> TrendResult:
    clean = sorted(
        {(int(year), float(value)) for year, value in series},
        key=lambda item: item[0],
    )

    if not clean:
        return TrendResult(
            direction="unknown",
            interpretation="unknown",
            confidence="low",
            slope_per_year=None,
            pct_change_1y=None,
            pct_change_3y=None,
            pct_change_5y=None,
            years_used=0,
            target_status=None,
        )

    current_year, current_value = clean[-1]
    by_year = {year: value for year, value in clean}

    changes = {
        horizon: _pct_change(current_value, by_year.get(current_year - horizon))
        for horizon in (1, 3, 5)
    }

    window = [(year, value) for year, value in clean if year >= current_year - 5]
    slope = _linear_slope(window)

    reference_year = None
    for horizon in (5, 3, 1):
        if current_year - horizon in by_year:
            reference_year = current_year - horizon
            break

    reference_value = by_year.get(reference_year) if reference_year is not None else None
    reference_change = (
        changes[5]
        if changes[5] is not None
        else changes[3]
        if changes[3] is not None
        else changes[1]
    )

    direction = _direction_from_change(reference_change)
    target_status = None

    if interpretation_policy == "target_range":
        if target_min is None or target_max is None:
            raise ValueError("target_range policy requires target_min and target_max")
        interpretation, target_status = _interpret_target_range(
            current_value,
            reference_value,
            target_min,
            target_max,
        )
    elif interpretation_policy in {"higher", "lower"}:
        interpretation = _interpret_directional(direction, interpretation_policy)
    else:
        interpretation = "neutral_or_contextual"

    if len(window) >= 5 and changes[5] is not None:
        confidence = "high"
    elif len(window) >= 3 and changes[3] is not None:
        confidence = "medium"
    else:
        confidence = "low"

    return TrendResult(
        direction=direction,
        interpretation=interpretation,
        confidence=confidence,
        slope_per_year=slope,
        pct_change_1y=changes[1],
        pct_change_3y=changes[3],
        pct_change_5y=changes[5],
        years_used=len(window),
        target_status=target_status,
    )
