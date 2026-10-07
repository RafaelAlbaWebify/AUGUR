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



def test_weighted_preference_index_keeps_tradeoff_on_pareto_frontier():
    snapshots = {
        "ESP": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 10.0, "ESP"),
            _row("housing_cost_overburden_rate", "Housing burden", "housing", 5.0, "ESP"),
        ],
        "IRL": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 5.0, "IRL"),
            _row("housing_cost_overburden_rate", "Housing burden", "housing", 10.0, "IRL"),
        ],
    }

    result = build_personalized_normalization(
        ["ESP", "IRL"],
        snapshots,
        {
            "decision_weight_productive_capacity": 4,
            "decision_weight_housing": 1,
        },
    )

    personalized = result["personalized"]
    assert personalized["status"] == "ready"
    assert round(personalized["scores"]["ESP"], 6) == 20.0
    assert round(personalized["scores"]["IRL"], 6) == 80.0
    assert set(personalized["pareto"]["frontier"]) == {"ESP", "IRL"}
    assert personalized["sensitivity"]["scenario_count"] > 1
    assert personalized["sensitivity"]["method"] == "joint_local_weight_neighborhood_plus_minus_1"
    assert personalized["sensitivity"]["truncated"] is False
    assert personalized["sensitivity"]["score_ranges"]["ESP"]["spread"] > 0
    assert personalized["sensitivity"]["rank_ranges"]["IRL"] == {
        "best_rank": 1,
        "worst_rank": 1,
        "top_scenario_count": personalized["sensitivity"]["scenario_count"],
        "scenario_count": personalized["sensitivity"]["scenario_count"],
        "status": "rank_stable",
    }


def test_pareto_frontier_excludes_strictly_dominated_country():
    snapshots = {
        "ESP": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 10.0, "ESP"),
            _row("housing_cost_overburden_rate", "Housing burden", "housing", 10.0, "ESP"),
        ],
        "IRL": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 5.0, "IRL"),
            _row("housing_cost_overburden_rate", "Housing burden", "housing", 5.0, "IRL"),
        ],
    }

    result = build_personalized_normalization(
        ["ESP", "IRL"],
        snapshots,
        {
            "decision_weight_productive_capacity": 3,
            "decision_weight_housing": 3,
        },
    )

    pareto = result["personalized"]["pareto"]
    assert pareto["frontier"] == ["IRL"]
    assert pareto["dominated_by"]["ESP"] == ["IRL"]
    assert pareto["dominated_by"]["IRL"] == []


def test_contextual_weight_blocks_preference_index_instead_of_imputing():
    snapshots = {
        "ESP": [
            _row("public_debt_gdp", "Debt", "fiscal", 100.0, "ESP"),
        ],
        "IRL": [
            _row("public_debt_gdp", "Debt", "fiscal", 50.0, "IRL"),
        ],
    }

    result = build_personalized_normalization(
        ["ESP", "IRL"],
        snapshots,
        {"decision_weight_fiscal": 5},
    )

    personalized = result["personalized"]
    assert result["status"] == "weight_evidence_blocked"
    assert personalized["status"] == "weight_evidence_blocked"
    assert personalized["scores"] == {}
    assert personalized["pareto"] is None
    assert personalized["blockers"] == [
        "fiscal:no_normalizable_dimension_evidence"
    ]


def test_all_zero_explicit_weights_do_not_create_score():
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
        {"decision_weight_productive_capacity": 0},
    )

    assert result["status"] == "no_positive_weights"
    assert result["personalized"]["scores"] == {}


def test_equal_tradeoff_is_preference_sensitive_under_weight_perturbation():
    snapshots = {
        "ESP": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 10.0, "ESP"),
            _row("housing_cost_overburden_rate", "Housing burden", "housing", 5.0, "ESP"),
        ],
        "IRL": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 5.0, "IRL"),
            _row("housing_cost_overburden_rate", "Housing burden", "housing", 10.0, "IRL"),
        ],
    }

    result = build_personalized_normalization(
        ["ESP", "IRL"],
        snapshots,
        {
            "decision_weight_productive_capacity": 1,
            "decision_weight_housing": 1,
        },
    )

    sensitivity = result["personalized"]["sensitivity"]
    assert sensitivity["rank_ranges"]["ESP"]["best_rank"] == 1
    assert sensitivity["rank_ranges"]["ESP"]["worst_rank"] == 2
    assert sensitivity["rank_ranges"]["ESP"]["status"] == "preference_sensitive"
    assert sensitivity["rank_ranges"]["IRL"]["best_rank"] == 1
    assert sensitivity["rank_ranges"]["IRL"]["worst_rank"] == 2
    assert sensitivity["rank_ranges"]["IRL"]["status"] == "preference_sensitive"



def test_joint_sensitivity_includes_simultaneous_weight_changes():
    snapshots = {
        "ESP": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 10.0, "ESP"),
            _row("housing_cost_overburden_rate", "Housing burden", "housing", 5.0, "ESP"),
        ],
        "IRL": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 5.0, "IRL"),
            _row("housing_cost_overburden_rate", "Housing burden", "housing", 10.0, "IRL"),
        ],
    }

    result = build_personalized_normalization(
        ["ESP", "IRL"],
        snapshots,
        {
            "decision_weight_productive_capacity": 2,
            "decision_weight_housing": 2,
        },
    )

    sensitivity = result["personalized"]["sensitivity"]

    assert sensitivity["method"] == "joint_local_weight_neighborhood_plus_minus_1"
    assert sensitivity["scenario_count"] == 9
    assert sensitivity["total_possible_scenarios"] == 9
    assert sensitivity["dimension_count"] == 2
    assert sensitivity["truncated"] is False
    assert any(
        scenario["weights"] == {
            "housing": 3.0,
            "productive_capacity": 3.0,
        }
        for scenario in sensitivity["scenarios"]
    )
    assert any(
        scenario["weights"] == {
            "housing": 1.0,
            "productive_capacity": 3.0,
        }
        for scenario in sensitivity["scenarios"]
    )


def test_joint_sensitivity_drops_all_zero_combination():
    snapshots = {
        "ESP": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 10.0, "ESP"),
            _row("housing_cost_overburden_rate", "Housing burden", "housing", 5.0, "ESP"),
        ],
        "IRL": [
            _row("unemployment_rate", "Unemployment", "productive_capacity", 5.0, "IRL"),
            _row("housing_cost_overburden_rate", "Housing burden", "housing", 10.0, "IRL"),
        ],
    }

    result = build_personalized_normalization(
        ["ESP", "IRL"],
        snapshots,
        {
            "decision_weight_productive_capacity": 1,
            "decision_weight_housing": 1,
        },
    )

    sensitivity = result["personalized"]["sensitivity"]
    assert sensitivity["cartesian_combination_count"] == 9
    assert sensitivity["total_possible_scenarios"] == 8
    assert sensitivity["scenario_count"] == 8
    assert sensitivity["truncated"] is False
    assert all(scenario["weights"] for scenario in sensitivity["scenarios"])
