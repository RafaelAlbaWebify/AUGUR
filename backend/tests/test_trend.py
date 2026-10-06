from app.engines.trend import calculate_trend


def test_higher_policy_increase_is_improving():
    result = calculate_trend(
        [(2020, 100), (2021, 102), (2022, 104), (2023, 106), (2024, 108), (2025, 110)],
        "higher",
    )

    assert result.direction in {"increase", "strong_increase"}
    assert result.interpretation == "improving"
    assert result.confidence == "high"
    assert result.evidence_depth == "high"
    assert result.trend_certainty == "high"
    assert result.linear_fit_r2 == 1.0
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


def test_country_trends_exposes_catalog_methodology_notes(monkeypatch):
    import app.services.trends as trends_service

    monkeypatch.setattr(
        trends_service,
        "indicator_registry",
        lambda: [{
            "indicator_id": "intentional_homicide_rate",
            "name": "Police-recorded intentional homicides",
            "dimension": "safety",
            "unit": "per_100k_people",
            "interpretation_policy": "lower",
            "target_min": None,
            "target_max": None,
        }],
    )
    monkeypatch.setattr(
        trends_service,
        "indicator_series",
        lambda _country, _indicator: [
            {"period": 2020, "value": 0.8, "source_id": "EUROSTAT"},
            {"period": 2021, "value": 0.7, "source_id": "EUROSTAT"},
            {"period": 2022, "value": 0.7, "source_id": "EUROSTAT"},
            {"period": 2023, "value": 0.6, "source_id": "EUROSTAT"},
            {"period": 2024, "value": 0.6, "source_id": "EUROSTAT"},
        ],
    )

    result = trends_service.country_trends("ESP")
    indicator = result["indicators"][0]

    assert "Police-recorded intentional homicide" in indicator["methodology_note"]
    assert "recording practices" in indicator["comparability_note"]


def test_evidence_depth_and_trend_certainty_are_separate():
    result = calculate_trend(
        [(2020, 100), (2021, 140), (2022, 90), (2023, 135), (2024, 95), (2025, 110)],
        "higher",
    )

    assert result.evidence_depth == "high"
    assert result.confidence == "high"
    assert result.trend_certainty == "low"
    assert result.linear_fit_r2 is not None
    assert result.linear_fit_r2 < 0.5


def test_short_but_consistent_series_has_low_depth_not_high_depth():
    result = calculate_trend(
        [(2023, 100), (2024, 110), (2025, 120)],
        "higher",
    )

    assert result.evidence_depth == "low"
    assert result.trend_certainty == "high"
    assert result.linear_fit_r2 == 1.0


def test_absolute_material_threshold_can_hold_small_rate_change_stable():
    result = calculate_trend(
        [(2020, 10.0), (2025, 10.3)],
        "lower",
        material_change_mode="absolute",
        material_change_threshold=0.5,
    )

    assert result.material_change_value == 0.3000000000000007
    assert result.direction == "stable"
    assert result.interpretation == "neutral_or_contextual"


def test_absolute_material_threshold_marks_larger_rate_change():
    result = calculate_trend(
        [(2020, 10.0), (2025, 10.7)],
        "lower",
        material_change_mode="absolute",
        material_change_threshold=0.5,
    )

    assert result.direction == "increase"
    assert result.interpretation == "deteriorating"


def test_relative_material_threshold_remains_available_for_scale_indicators():
    result = calculate_trend(
        [(2020, 100.0), (2025, 100.4)],
        "higher",
        material_change_mode="relative_pct",
        material_change_threshold=0.5,
    )

    assert result.direction == "stable"
    assert result.material_change_mode == "relative_pct"


def test_country_trends_exposes_material_change_rule(monkeypatch):
    import app.services.trends as trends_service

    monkeypatch.setattr(
        trends_service,
        "indicator_registry",
        lambda: [{
            "indicator_id": "unemployment_rate",
            "name": "Unemployment rate",
            "dimension": "productive_capacity",
            "unit": "percent",
            "interpretation_policy": "lower",
            "target_min": None,
            "target_max": None,
        }],
    )
    monkeypatch.setattr(
        trends_service,
        "indicator_series",
        lambda _country, _indicator: [
            {"period": 2020, "value": 10.0, "source_id": "EUROSTAT"},
            {"period": 2025, "value": 10.3, "source_id": "EUROSTAT"},
        ],
    )

    result = trends_service.country_trends("ESP")
    indicator = result["indicators"][0]

    assert indicator["material_change_rule"]["mode"] == "absolute"
    assert indicator["material_change_rule"]["threshold"] == 0.5
    assert indicator["trend"]["direction"] == "stable"
