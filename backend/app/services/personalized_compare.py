from __future__ import annotations

from collections import defaultdict

from app.catalog import (
    INDICATORS,
    SYNTHESIS_CONSTRUCTS,
    SYNTHESIS_CONSTRUCT_VERSION,
)
from app.db.analytics import latest_observations
from app.db.profile import get_profile


WEIGHT_PREFIX = "decision_weight_"
WEIGHT_MIN = 0.0
WEIGHT_MAX = 5.0
NORMALIZATION_VERSION = "augur_selected_set_utility_v1"

INDICATOR_META = {
    item["indicator_id"]: item
    for item in INDICATORS
}
DECISION_DIMENSIONS = sorted({
    item["dimension"]
    for item in INDICATORS
})


def explicit_dimension_weights(preferences: dict) -> dict:
    weights: dict[str, float] = {}
    for dimension in DECISION_DIMENSIONS:
        raw = preferences.get(f"{WEIGHT_PREFIX}{dimension}")
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            continue
        value = float(raw)
        if value < WEIGHT_MIN or value > WEIGHT_MAX:
            continue
        weights[dimension] = value
    return weights


def _selected_set_utility(
    values: dict[str, float],
    policy: str,
    target_min: float | None,
    target_max: float | None,
) -> tuple[dict[str, float], dict]:
    if not values:
        return {}, {"status": "no_values"}

    numeric = list(values.values())
    minimum = min(numeric)
    maximum = max(numeric)

    if policy == "contextual":
        return {}, {
            "status": "excluded_contextual",
            "policy": policy,
        }

    if policy in {"higher", "lower"}:
        if abs(maximum - minimum) < 1e-12:
            utilities = {country: 0.5 for country in values}
            return utilities, {
                "status": "aligned",
                "policy": policy,
                "selected_min": minimum,
                "selected_max": maximum,
                "formula": "equal_values=>0.5",
            }

        span = maximum - minimum
        if policy == "higher":
            utilities = {
                country: (value - minimum) / span
                for country, value in values.items()
            }
            formula = "(value-min)/(max-min)"
        else:
            utilities = {
                country: (maximum - value) / span
                for country, value in values.items()
            }
            formula = "(max-value)/(max-min)"

        return utilities, {
            "status": "normalized",
            "policy": policy,
            "selected_min": minimum,
            "selected_max": maximum,
            "formula": formula,
        }

    if policy == "target_range":
        if target_min is None or target_max is None:
            return {}, {
                "status": "excluded_missing_target_range",
                "policy": policy,
            }

        def distance(value: float) -> float:
            if target_min <= value <= target_max:
                return 0.0
            if value < target_min:
                return target_min - value
            return value - target_max

        distances = {
            country: distance(value)
            for country, value in values.items()
        }
        max_distance = max(distances.values())

        if max_distance < 1e-12:
            utilities = {country: 1.0 for country in values}
        elif len(set(round(item, 12) for item in distances.values())) == 1:
            utilities = {country: 0.5 for country in values}
        else:
            utilities = {
                country: 1.0 - (item / max_distance)
                for country, item in distances.items()
            }

        return utilities, {
            "status": "normalized",
            "policy": policy,
            "target_min": target_min,
            "target_max": target_max,
            "max_selected_distance_from_target": max_distance,
            "formula": "1-distance_to_target_range/max_selected_distance",
        }

    return {}, {
        "status": "excluded_unknown_policy",
        "policy": policy,
    }


def _score_countries(
    countries: list[str],
    dimension_by_id: dict[str, dict],
    weights: dict[str, float],
) -> dict[str, float]:
    total_weight = sum(weights.values())
    if total_weight <= 0:
        return {}

    return {
        country: 100.0 * sum(
            (weight / total_weight)
            * float(dimension_by_id[dimension]["utility"][country])
            for dimension, weight in weights.items()
        )
        for country in countries
    }


def _pareto_analysis(
    countries: list[str],
    dimension_by_id: dict[str, dict],
    dimensions: list[str],
) -> dict:
    dominated_by: dict[str, list[str]] = {
        country: []
        for country in countries
    }

    for candidate in countries:
        for challenger in countries:
            if candidate == challenger:
                continue

            candidate_values = [
                float(dimension_by_id[dimension]["utility"][candidate])
                for dimension in dimensions
            ]
            challenger_values = [
                float(dimension_by_id[dimension]["utility"][challenger])
                for dimension in dimensions
            ]
            no_worse = all(
                challenger >= current
                for challenger, current in zip(
                    challenger_values,
                    candidate_values,
                )
            )
            strictly_better = any(
                challenger > current + 1e-12
                for challenger, current in zip(
                    challenger_values,
                    candidate_values,
                )
            )
            if no_worse and strictly_better:
                dominated_by[candidate].append(challenger)

    frontier = [
        country
        for country in countries
        if not dominated_by[country]
    ]

    return {
        "method": "pareto_nondominance_on_positive_weight_dimensions",
        "dimensions": dimensions,
        "frontier": frontier,
        "dominated_by": dominated_by,
        "notes": [
            "Pareto membership is not a universal best-country claim.",
            "A country is dominated only when another is no worse on every included dimension and strictly better on at least one.",
        ],
    }


def _sensitivity_analysis(
    countries: list[str],
    dimension_by_id: dict[str, dict],
    weights: dict[str, float],
) -> dict:
    scenarios = [
        {
            "id": "base",
            "weights": dict(weights),
            "scores": _score_countries(
                countries,
                dimension_by_id,
                weights,
            ),
        }
    ]

    for dimension, current in sorted(weights.items()):
        for delta, suffix in ((-1.0, "minus_1"), (1.0, "plus_1")):
            updated = min(
                WEIGHT_MAX,
                max(WEIGHT_MIN, current + delta),
            )
            if abs(updated - current) < 1e-12:
                continue
            scenario_weights = dict(weights)
            if updated <= 0:
                scenario_weights.pop(dimension, None)
            else:
                scenario_weights[dimension] = updated
            if not scenario_weights:
                continue
            scenarios.append({
                "id": f"{dimension}_{suffix}",
                "weights": scenario_weights,
                "scores": _score_countries(
                    countries,
                    dimension_by_id,
                    scenario_weights,
                ),
            })

    ranges = {}
    for country in countries:
        values = [
            float(scenario["scores"][country])
            for scenario in scenarios
            if country in scenario["scores"]
        ]
        ranges[country] = {
            "min": min(values),
            "max": max(values),
            "spread": max(values) - min(values),
        }

    return {
        "method": "one_at_a_time_weight_perturbation_plus_minus_1",
        "scenario_count": len(scenarios),
        "weight_bounds": [WEIGHT_MIN, WEIGHT_MAX],
        "score_ranges": ranges,
        "scenarios": scenarios,
        "notes": [
            "Sensitivity varies one explicit positive weight by ±1 within the 0–5 scale while holding all others fixed.",
            "These ranges measure preference-weight sensitivity, not statistical uncertainty in the underlying evidence.",
        ],
    }


def _personalized_decision_layer(
    countries: list[str],
    weights: dict[str, float],
    dimensions: list[dict],
) -> dict:
    positive_weights = {
        dimension: weight
        for dimension, weight in weights.items()
        if weight > 0
    }

    if not weights:
        return {
            "status": "weights_missing",
            "scores": {},
            "blockers": ["explicit_dimension_weights_missing"],
            "pareto": None,
            "sensitivity": None,
        }

    if not positive_weights:
        return {
            "status": "no_positive_weights",
            "scores": {},
            "blockers": ["all_explicit_dimension_weights_are_zero"],
            "pareto": None,
            "sensitivity": None,
        }

    dimension_by_id = {
        item["dimension"]: item
        for item in dimensions
    }
    blockers = []

    for dimension in positive_weights:
        item = dimension_by_id.get(dimension)
        if item is None:
            blockers.append(
                f"{dimension}:no_normalizable_dimension_evidence"
            )
            continue
        missing = [
            country
            for country in countries
            if country not in item["utility"]
        ]
        if missing:
            blockers.append(
                f"{dimension}:missing_country_utility:{','.join(missing)}"
            )

    if blockers:
        return {
            "status": "weight_evidence_blocked",
            "scores": {},
            "blockers": blockers,
            "positive_weights": positive_weights,
            "pareto": None,
            "sensitivity": None,
            "notes": [
                "AUGUR does not impute missing or contextual dimension utilities merely because the user assigned them a weight.",
            ],
        }

    scores = _score_countries(
        countries,
        dimension_by_id,
        positive_weights,
    )
    normalized_weights = {
        dimension: weight / sum(positive_weights.values())
        for dimension, weight in positive_weights.items()
    }
    included_dimensions = sorted(positive_weights)

    return {
        "status": "ready",
        "score_label": "selected_set_preference_fit_index",
        "score_range": [0.0, 100.0],
        "scores": scores,
        "positive_weights": positive_weights,
        "normalized_weights": normalized_weights,
        "included_dimensions": included_dimensions,
        "coverage": {
            country: 1.0
            for country in countries
        },
        "sensitivity": _sensitivity_analysis(
            countries,
            dimension_by_id,
            positive_weights,
        ),
        "pareto": _pareto_analysis(
            countries,
            dimension_by_id,
            included_dimensions,
        ),
        "notes": [
            "The preference-fit index is relative to the selected country set and the user's explicit weights.",
            "It is not an absolute country score and must not be compared across different selected sets or weight profiles.",
            "No universal winner is declared; Pareto frontier and sensitivity should be considered alongside the index.",
        ],
    }


def build_personalized_normalization(
    country_iso3s: list[str],
    snapshots: dict[str, list[dict]],
    preferences: dict,
) -> dict:
    countries = [code.upper() for code in country_iso3s]
    weights = explicit_dimension_weights(preferences)

    indicator_rows: dict[str, dict] = {}
    for country in countries:
        for row in snapshots.get(country, []):
            indicator_rows.setdefault(
                row["indicator_id"],
                {
                    "indicator_id": row["indicator_id"],
                    "name": row["name"],
                    "dimension": row["dimension"],
                    "unit": row["unit"],
                    "countries": {},
                },
            )["countries"][country] = {
                "value": float(row["value"]),
                "period": row["period"],
                "source_id": row["source_id"],
            }

    normalized_indicators = []
    construct_values: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for indicator_id, row in sorted(indicator_rows.items()):
        meta = INDICATOR_META.get(indicator_id)
        if meta is None:
            continue

        values = {
            country: payload["value"]
            for country, payload in row["countries"].items()
        }
        utilities, normalization = _selected_set_utility(
            values,
            meta["interpretation_policy"],
            meta.get("target_min"),
            meta.get("target_max"),
        )
        construct = SYNTHESIS_CONSTRUCTS.get(indicator_id, indicator_id)

        if utilities:
            for country, utility in utilities.items():
                construct_values[(row["dimension"], construct)][country].append(
                    utility
                )

        normalized_indicators.append({
            **row,
            "interpretation_policy": meta["interpretation_policy"],
            "target_min": meta.get("target_min"),
            "target_max": meta.get("target_max"),
            "synthesis_construct": construct,
            "normalization": normalization,
            "utility": utilities,
        })

    constructs = []
    dimension_constructs: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for (dimension, construct), by_country in sorted(construct_values.items()):
        utilities = {
            country: sum(items) / len(items)
            for country, items in by_country.items()
            if items
        }
        for country, utility in utilities.items():
            dimension_constructs[dimension][country].append(utility)

        members = sorted(
            row["indicator_id"]
            for row in normalized_indicators
            if row["dimension"] == dimension
            and row["synthesis_construct"] == construct
            and row["utility"]
        )
        constructs.append({
            "dimension": dimension,
            "construct": construct,
            "indicator_ids": members,
            "utility": utilities,
            "method": "mean_of_available_normalized_indicators_within_construct",
        })

    dimensions = []
    for dimension, by_country in sorted(dimension_constructs.items()):
        utilities = {
            country: sum(items) / len(items)
            for country, items in by_country.items()
            if items
        }
        dimensions.append({
            "dimension": dimension,
            "explicit_weight": weights.get(dimension),
            "utility": utilities,
            "construct_count": sum(
                1 for item in constructs
                if item["dimension"] == dimension
            ),
            "method": "mean_of_available_semantic_construct_utilities",
        })

    personalized = _personalized_decision_layer(
        countries,
        weights,
        dimensions,
    )

    return {
        "status": personalized["status"],
        "countries": countries,
        "weights": {
            "explicit": weights,
            "scale": [WEIGHT_MIN, WEIGHT_MAX],
            "missing_means": "not_selected_for_personal_weighting",
        },
        "normalization": {
            "version": NORMALIZATION_VERSION,
            "scope": "selected_country_set",
            "utility_range": [0.0, 1.0],
            "contextual_indicators_excluded": True,
            "semantic_construct_version": SYNTHESIS_CONSTRUCT_VERSION,
            "notes": [
                "Raw evidence is never modified by personal preferences.",
                "Utilities are relative to the currently selected country set and must not be compared across different selected sets as absolute scores.",
                "Semantic constructs prevent duplicate source series for the same concept from receiving independent dimension weight.",
                "No overall personalized ranking is produced by this P2.1/P2.2 layer.",
            ],
        },
        "indicators": normalized_indicators,
        "constructs": constructs,
        "dimensions": dimensions,
        "personalized": personalized,
    }


def personalized_normalization(country_iso3s: list[str]) -> dict:
    countries = [code.upper() for code in country_iso3s]
    snapshots = {
        code: latest_observations(code)
        for code in countries
    }
    profile = get_profile()
    return build_personalized_normalization(
        countries,
        snapshots,
        profile.preferences,
    )
