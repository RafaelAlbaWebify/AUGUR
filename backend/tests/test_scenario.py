from app.engines.scenario import build_scenario_value


def test_growth_scenario_envelope():
    result = build_scenario_value("real_gdp_growth", 2.0)
    assert result.baseline == 2.0
    assert result.improvement == 2.5
    assert result.stress == 1.25


def test_unemployment_scenario_envelope():
    result = build_scenario_value("imf_unemployment_rate", 10.0)
    assert result.improvement == 9.0
    assert result.stress == 11.5


def test_contextual_indicator_is_not_directionally_adjusted():
    result = build_scenario_value("population_total", 50_000_000)
    assert result.baseline == result.improvement == result.stress


def test_inflation_improvement_moves_toward_midpoint():
    result = build_scenario_value(
        "imf_inflation_average",
        4.0,
        target_min=1.0,
        target_max=3.0,
    )
    assert result.improvement == 3.0
    assert result.stress == 5.5
