from app.engines.dimension import summarize_dimension


def make_indicator(indicator_id: str, interpretation: str, direction: str = "increase", confidence: str = "high"):
    return {
        "indicator_id": indicator_id,
        "name": indicator_id,
        "trend": {
            "interpretation": interpretation,
            "direction": direction,
            "confidence": confidence,
            "pct_change_5y": 5.0,
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
