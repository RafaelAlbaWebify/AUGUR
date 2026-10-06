from __future__ import annotations

from collections import defaultdict


CONFIDENCE_VALUES = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


def _confidence_label(value: float) -> str:
    if value >= 2.5:
        return "high"
    if value >= 1.5:
        return "medium"
    return "low"


def summarize_dimension(indicators: list[dict]) -> dict:
    improving = []
    deteriorating = []
    stable = []
    contextual = []
    by_construct: dict[str, list[dict]] = defaultdict(list)

    for indicator in indicators:
        trend = indicator.get("trend") or {}
        interpretation = trend.get("interpretation")
        direction = trend.get("direction")
        construct = indicator.get("synthesis_construct") or indicator["indicator_id"]

        signal = {
            "indicator_id": indicator["indicator_id"],
            "name": indicator["name"],
            "direction": direction,
            "confidence": trend.get("confidence", "low"),
            "evidence_depth": trend.get("evidence_depth", trend.get("confidence", "low")),
            "trend_certainty": trend.get("trend_certainty", "low"),
            "pct_change_5y": trend.get("pct_change_5y"),
            "target_status": trend.get("target_status"),
            "synthesis_construct": construct,
        }

        if interpretation == "improving":
            category = "improving"
            improving.append(signal)
        elif interpretation == "deteriorating":
            category = "deteriorating"
            deteriorating.append(signal)
        elif interpretation == "within_target" or direction == "stable":
            category = "stable"
            stable.append(signal)
        else:
            category = "contextual"
            contextual.append(signal)

        by_construct[construct].append({
            "category": category,
            "signal": signal,
        })

    construct_summaries = []
    for construct, members in sorted(by_construct.items()):
        directional_categories = {
            member["category"]
            for member in members
            if member["category"] != "contextual"
        }

        if "improving" in directional_categories and "deteriorating" in directional_categories:
            state = "conflicting"
        elif "improving" in directional_categories:
            state = "improving"
        elif "deteriorating" in directional_categories:
            state = "deteriorating"
        elif "stable" in directional_categories:
            state = "stable"
        else:
            state = "contextual"

        confidence_values = [
            CONFIDENCE_VALUES.get(member["signal"]["confidence"], 1)
            for member in members
        ]
        construct_summaries.append({
            "construct": construct,
            "state": state,
            "indicator_ids": [member["signal"]["indicator_id"] for member in members],
            "indicator_count": len(members),
            "confidence": _confidence_label(
                sum(confidence_values) / len(confidence_values)
                if confidence_values
                else 1
            ),
        })

    effective_improving = [
        item for item in construct_summaries if item["state"] == "improving"
    ]
    effective_deteriorating = [
        item for item in construct_summaries if item["state"] == "deteriorating"
    ]
    effective_stable = [
        item for item in construct_summaries if item["state"] == "stable"
    ]
    conflicting_constructs = [
        item for item in construct_summaries if item["state"] == "conflicting"
    ]

    effective_directional_count = (
        len(effective_improving)
        + len(effective_deteriorating)
        + len(effective_stable)
        + len(conflicting_constructs)
    )
    total_construct_count = len(construct_summaries)
    raw_directional_count = len(improving) + len(deteriorating) + len(stable)
    total_count = len(indicators)

    if conflicting_constructs or (effective_improving and effective_deteriorating):
        trajectory = "mixed"
    elif len(effective_improving) == 1 and effective_directional_count == 1:
        trajectory = "limited_evidence"
    elif len(effective_deteriorating) == 1 and effective_directional_count == 1:
        trajectory = "limited_evidence"
    elif effective_improving:
        trajectory = "improving"
    elif effective_deteriorating:
        trajectory = "deteriorating"
    elif effective_stable:
        trajectory = "stable"
    else:
        trajectory = "contextual"

    construct_confidences = [
        CONFIDENCE_VALUES.get(item["confidence"], 1)
        for item in construct_summaries
    ]
    avg_confidence = (
        sum(construct_confidences) / len(construct_confidences)
        if construct_confidences
        else 1
    )
    confidence = _confidence_label(avg_confidence)

    if trajectory == "limited_evidence":
        confidence = "low"

    duplicate_constructs = [
        item for item in construct_summaries
        if item["indicator_count"] > 1
    ]

    return {
        "trajectory": trajectory,
        "confidence": confidence,
        "indicator_count": total_count,
        "directional_indicator_count": raw_directional_count,
        "synthesis_construct_count": total_construct_count,
        "effective_directional_construct_count": effective_directional_count,
        "coverage": (
            effective_directional_count / total_construct_count
            if total_construct_count
            else 0.0
        ),
        "evidence_status": (
            "sufficient"
            if effective_directional_count >= 2
            else "limited"
            if effective_directional_count == 1
            else "contextual_only"
        ),
        "evidence_note": (
            "Broad dimension trajectory requires at least two independent directional constructs."
            if effective_directional_count == 1
            else "Conflicting indicators inside the same construct prevent a single directional conclusion."
            if conflicting_constructs
            else None
        ),
        "duplicate_constructs": duplicate_constructs,
        "conflicting_constructs": conflicting_constructs,
        "constructs": construct_summaries,
        "improving_signals": improving,
        "deteriorating_signals": deteriorating,
        "stable_signals": stable,
        "contextual_signals": contextual,
    }
