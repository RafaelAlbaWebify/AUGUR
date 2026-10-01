from __future__ import annotations


CONFIDENCE_VALUES = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


def summarize_dimension(indicators: list[dict]) -> dict:
    improving = []
    deteriorating = []
    stable = []
    contextual = []

    for indicator in indicators:
        trend = indicator.get("trend") or {}
        interpretation = trend.get("interpretation")
        direction = trend.get("direction")

        signal = {
            "indicator_id": indicator["indicator_id"],
            "name": indicator["name"],
            "direction": direction,
            "confidence": trend.get("confidence", "low"),
            "pct_change_5y": trend.get("pct_change_5y"),
            "target_status": trend.get("target_status"),
        }

        if interpretation == "improving":
            improving.append(signal)
        elif interpretation == "deteriorating":
            deteriorating.append(signal)
        elif interpretation == "within_target" or direction == "stable":
            stable.append(signal)
        else:
            contextual.append(signal)

    directional_count = len(improving) + len(deteriorating) + len(stable)
    total_count = len(indicators)

    if directional_count == 1:
        trajectory = "limited_evidence"
    elif improving and not deteriorating:
        trajectory = "improving"
    elif deteriorating and not improving:
        trajectory = "deteriorating"
    elif improving and deteriorating:
        trajectory = "mixed"
    elif stable:
        trajectory = "stable"
    else:
        trajectory = "contextual"

    confidences = [
        CONFIDENCE_VALUES.get(
            (indicator.get("trend") or {}).get("confidence", "low"),
            1,
        )
        for indicator in indicators
    ]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 1

    if avg_confidence >= 2.5:
        confidence = "high"
    elif avg_confidence >= 1.5:
        confidence = "medium"
    else:
        confidence = "low"

    if trajectory == "limited_evidence":
        confidence = "low"

    return {
        "trajectory": trajectory,
        "confidence": confidence,
        "indicator_count": total_count,
        "directional_indicator_count": directional_count,
        "coverage": (
            directional_count / total_count
            if total_count
            else 0.0
        ),
        "evidence_status": (
            "sufficient"
            if directional_count >= 2
            else "limited"
            if directional_count == 1
            else "contextual_only"
        ),
        "evidence_note": (
            "Broad dimension trajectory requires at least two directional signals."
            if directional_count == 1
            else None
        ),
        "improving_signals": improving,
        "deteriorating_signals": deteriorating,
        "stable_signals": stable,
        "contextual_signals": contextual,
    }
