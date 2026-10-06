from app.engines.dimension import summarize_dimension


def make_indicator(
    indicator_id: str,
    interpretation: str,
    direction: str = "increase",
    confidence: str = "high",
    target_status: str | None = None,
):
    return {
        "indicator_id": indicator_id,
        "name": indicator_id,
        "trend": {
            "interpretation": interpretation,
            "direction": direction,
            "confidence": confidence,
            "pct_change_5y": 5.0,
            "target_status": target_status,
        },
    }


def test_dimension_improving_when_only_positive_directional_signals():
    result = summarize_dimension([
        make_indicator("a", "improving"),
        make_indicator("b", "improving"),
    ])

    assert result["trajectory"] == "improving"
    assert result["coverage"] == 1.0


def test_dimension_mixed_when_signals_disagree():
    result = summarize_dimension([
        make_indicator("a", "improving"),
        make_indicator("b", "deteriorating", direction="decrease"),
    ])

    assert result["trajectory"] == "mixed"


def test_dimension_contextual_when_no_directional_interpretation():
    result = summarize_dimension([
        make_indicator("a", "neutral_or_contextual"),
        make_indicator("b", "neutral_or_contextual", direction="decrease"),
    ])

    assert result["trajectory"] == "contextual"
    assert result["directional_indicator_count"] == 0


def test_within_target_counts_as_stable_signal():
    result = summarize_dimension([
        make_indicator(
            "inflation",
            "within_target",
            direction="increase",
            target_status="within_target",
        ),
    ])

    assert result["trajectory"] == "stable"
    assert result["directional_indicator_count"] == 1



def test_single_directional_signal_is_limited_evidence():
    result = summarize_dimension([
        make_indicator("housing_cost_overburden_rate", "improving"),
    ])

    assert result["trajectory"] == "limited_evidence"
    assert result["confidence"] == "low"
    assert result["directional_indicator_count"] == 1
    assert result["evidence_status"] == "limited"
    assert result["evidence_note"]


def test_two_directional_signals_can_define_broad_trajectory():
    result = summarize_dimension([
        make_indicator("a", "improving"),
        make_indicator("b", "improving"),
    ])

    assert result["trajectory"] == "improving"
    assert result["evidence_status"] == "sufficient"



def test_housing_mixed_when_burden_improves_but_market_pressure_worsens():
    result = summarize_dimension([
        make_indicator(
            "housing_cost_overburden_rate",
            "improving",
            direction="decrease",
        ),
        make_indicator(
            "real_house_price_index",
            "deteriorating",
            direction="increase",
        ),
        make_indicator(
            "rent_price_index",
            "deteriorating",
            direction="increase",
        ),
    ])

    assert result["trajectory"] == "mixed"
    assert result["directional_indicator_count"] == 3
    assert result["evidence_status"] == "sufficient"
    assert len(result["improving_signals"]) == 1
    assert len(result["deteriorating_signals"]) == 2


def test_duplicate_indicators_count_as_one_construct_vote():
    first = make_indicator("unemployment_rate", "improving", direction="decrease")
    second = make_indicator("imf_unemployment_rate", "improving", direction="decrease")
    first["synthesis_construct"] = "unemployment_rate"
    second["synthesis_construct"] = "unemployment_rate"

    result = summarize_dimension([first, second])

    assert result["directional_indicator_count"] == 2
    assert result["effective_directional_construct_count"] == 1
    assert result["synthesis_construct_count"] == 1
    assert result["trajectory"] == "limited_evidence"
    assert result["evidence_status"] == "limited"
    assert len(result["duplicate_constructs"]) == 1


def test_conflicting_duplicate_sources_do_not_become_two_votes():
    first = make_indicator("inflation_hicp", "improving", direction="decrease")
    second = make_indicator("inflation_cpi", "deteriorating", direction="increase")
    first["synthesis_construct"] = "inflation_rate"
    second["synthesis_construct"] = "inflation_rate"

    result = summarize_dimension([first, second])

    assert result["effective_directional_construct_count"] == 1
    assert result["trajectory"] == "mixed"
    assert result["evidence_status"] == "limited"
    assert result["conflicting_constructs"][0]["construct"] == "inflation_rate"


def test_independent_constructs_can_still_define_dimension_trajectory():
    first = make_indicator("employment_rate_20_64", "improving")
    second = make_indicator("unemployment_rate", "improving", direction="decrease")
    first["synthesis_construct"] = "employment_rate_20_64"
    second["synthesis_construct"] = "unemployment_rate"

    result = summarize_dimension([first, second])

    assert result["effective_directional_construct_count"] == 2
    assert result["trajectory"] == "improving"
    assert result["evidence_status"] == "sufficient"
