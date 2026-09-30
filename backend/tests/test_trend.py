from app.engines.trend import calculate_trend


def test_higher_policy_increase_is_improving():
    result = calculate_trend(
        [(2020, 100), (2021, 102), (2022, 104), (2023, 106), (2024, 108), (2025, 110)],
        "higher",
    )

    assert result.direction in {"increase", "strong_increase"}
    assert result.interpretation == "improving"
    assert result.confidence == "high"
    assert result.pct_change_5y == 10.0


def test_lower_policy_increase_is_deteriorating():
    result = calculate_trend(
        [(2020, 10), (2021, 11), (2022, 12), (2023, 13), (2024, 14), (2025, 15)],
        "lower",
    )

    assert result.interpretation == "deteriorating"


def test_contextual_indicator_is_not_forced_positive_or_negative():
    result = calculate_trend(
        [(2020, 100), (2021, 105), (2022, 110), (2023, 115), (2024, 120), (2025, 125)],
        "contextual",
    )

    assert result.interpretation == "neutral_or_contextual"


def test_target_range_reports_within_target():
    result = calculate_trend(
        [(2020, 0.5), (2021, 1.2), (2022, 4.0), (2023, 3.5), (2024, 3.2), (2025, 2.7)],
        "target_range",
        1.0,
        3.0,
    )

    assert result.interpretation == "within_target"
    assert result.target_status == "within_target"


def test_target_range_improves_when_moving_closer():
    result = calculate_trend(
        [(2020, 8.0), (2021, 7.0), (2022, 6.0), (2023, 5.0), (2024, 4.0), (2025, 3.5)],
        "target_range",
        1.0,
        3.0,
    )

    assert result.interpretation == "improving"
    assert result.target_status == "above_target"


def test_target_range_requires_bounds():
    try:
        calculate_trend([(2024, 2.0), (2025, 2.5)], "target_range")
    except ValueError as exc:
        assert "target_min" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
