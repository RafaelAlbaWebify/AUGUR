from app.engines.trend import calculate_trend


def test_higher_is_better_increase_is_improving():
    result = calculate_trend(
        [(2020, 100), (2021, 102), (2022, 104), (2023, 106), (2024, 108), (2025, 110)],
        True,
    )

    assert result.direction in {"increase", "strong_increase"}
    assert result.interpretation == "improving"
    assert result.confidence == "high"
    assert result.pct_change_5y == 10.0


def test_lower_is_better_increase_is_deteriorating():
    result = calculate_trend(
        [(2020, 10), (2021, 11), (2022, 12), (2023, 13), (2024, 14), (2025, 15)],
        False,
    )

    assert result.interpretation == "deteriorating"


def test_contextual_indicator_is_not_forced_positive_or_negative():
    result = calculate_trend(
        [(2020, 100), (2021, 105), (2022, 110), (2023, 115), (2024, 120), (2025, 125)],
        None,
    )

    assert result.interpretation == "neutral_or_contextual"
