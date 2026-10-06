from app.services.personalized_compare import (
    _selected_set_utility,
    build_personalized_normalization,
    explicit_dimension_weights,
)


def _row(indicator_id, name, dimension, value, country):
    return {
        "indicator_id": indicator_id,
        "name": name,
        "dimension": dimension,
        "unit": "percent",
        "period": 2025,
        "value": value,
        "source_id": "TEST",
        "country": country,
    }


def test_explicit_weights_ignore_booleans_and_out_of_range_values():
    result = explicit_dimension_weights({
        "decision_weight_housing": 5,
        "decision_weight_safety": 2.5,
        "decision_weight_prosperity": True,
        "decision_weight_environment": 7,
        "priority_housing": True,
    })

    assert result == {
        "housing": 5.0,
        "safety": 2.5,
    }


def test_higher_and_lower_normalization_are_directional():
    higher, _ = _selected_set_utility(
        {"ESP": 10.0, "IRL": 20.0},
        "higher",
        None,
        None,
    )
    lower, _ = _selected_set_utility(
        {"ESP": 10.0, "IRL": 20.0},
        "lower",
        None,
        None,
    )

    assert higher == {"ESP": 0.0, "IRL": 1.0}
    assert lower == {"ESP": 1.0, "IRL": 0.0}


def test_target_range_rewards_values_inside_range():
    utility, metadata = _selected_set_utility(
        {"ESP": 2.0, "IRL": 5.0, "PRT": 1.0},
        "target_range",
        1.0,
        3.0,
    )

    assert utility["ESP"] == 1.0
    assert utility["PRT"] == 1.0
    assert utility["IRL"] == 0.0
    assert metadata["target_min"] == 1.0
    assert metadata["target_max"] == 3.0


def test_contextual_indicator_is_excluded():
    utility, metadata = _selected_set_utility(
        {"ESP": 10.0, "IRL": 20.0},
        "contextual",
        None,
        None,
    )

    assert utility == {}
    assert metadata["status"] == "excluded_contextual"


def test_semantic_duplicate_series_collapse_before_dimension_mean():
    snapshots = {
        "ESP": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 10.0, "ESP"),
            _row("imf_unemployment_rate", "IMF unemployment", "productive_capacity", 8.0, "ESP"),
            _row("employment_rate_20_64", "Employment", "productive_capacity", 70.0, "ESP"),
        ],
        "IRL": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 5.0, "IRL"),
            _row("imf_unemployment_rate", "IMF unemployment", "productive_capacity", 4.0, "IRL"),
            _row("employment_rate_20_64", "Employment", "productive_capacity", 80.0, "IRL"),
        ],
    }

    result = build_personalized_normalization(
        ["ESP", "IRL"],
        snapshots,
        {"decision_weight_productive_capacity": 5},
    )

    dimension = next(
        item for item in result["dimensions"]
        if item["dimension"] == "productive_capacity"
    )
    unemployment = next(
        item for item in result["constructs"]
        if item["construct"] == "unemployment_rate"
    )

    assert unemployment["indicator_ids"] == [
        "imf_unemployment_rate",
        "unemployment_rate",
    ]
    assert dimension["construct_count"] == 2
    assert dimension["utility"]["ESP"] == 0.0
    assert dimension["utility"]["IRL"] == 1.0
    assert result["status"] == "ready"


def test_no_explicit_weights_keeps_normalization_but_blocks_personal_weighting():
    snapshots = {
        "ESP": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 10.0, "ESP"),
        ],
        "IRL": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 5.0, "IRL"),
        ],
    }

    result = build_personalized_normalization(
        ["ESP", "IRL"],
        snapshots,
        {},
    )

    assert result["status"] == "weights_missing"
    assert result["dimensions"][0]["utility"]["IRL"] == 1.0
    assert "ranking" not in result
