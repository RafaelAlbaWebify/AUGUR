from app.engines.scenario import build_scenario_value, horizon_uncertainty
from app.services.scenarios import country_scenarios


def test_horizon_uncertainty_scales_outward():
    assert horizon_uncertainty(2030) == (1.0, "near")
    assert horizon_uncertainty(2035) == (1.5, "medium")
    assert horizon_uncertainty(2045) == (2.5, "long")


def test_growth_scenario_envelope():
    result = build_scenario_value("real_gdp_growth", 2.0, 2030)
    assert result.baseline == 2.0
    assert result.improvement == 2.5
    assert result.stress == 1.25


def test_growth_envelope_widens_with_horizon():
    near = build_scenario_value("real_gdp_growth", 2.0, 2030)
    long = build_scenario_value("real_gdp_growth", 2.0, 2045)

    assert long.improvement - long.baseline > near.improvement - near.baseline
    assert long.baseline - long.stress > near.baseline - near.stress


def test_unemployment_scenario_envelope():
    result = build_scenario_value("imf_unemployment_rate", 10.0, 2030)
    assert result.improvement == 9.0
    assert result.stress == 11.5


def test_contextual_indicator_is_not_directionally_adjusted():
    result = build_scenario_value("population_total", 50_000_000, 2045)
    assert result.baseline == result.improvement == result.stress
    assert result.uncertainty_level == "long"


def test_inflation_improvement_moves_toward_midpoint():
    result = build_scenario_value(
        "imf_inflation_average",
        4.0,
        2030,
        target_min=1.0,
        target_max=3.0,
    )
    assert result.improvement == 3.0
    assert result.stress == 5.5


def test_life_expectancy_envelope_widens():
    near = build_scenario_value("life_expectancy", 85.0, 2030)
    long = build_scenario_value("life_expectancy", 85.0, 2045)

    assert near.improvement == 85.8
    assert long.improvement == 87.0
    assert long.stress == 83.0


def test_country_scenarios_declares_experimental_model_status(monkeypatch):
    import app.services.scenarios as scenarios_service

    monkeypatch.setattr(
        scenarios_service,
        "future_trajectory",
        lambda _country, _horizons: [],
    )

    result = country_scenarios("ESP")

    assert result["model_status"] == {
        "state": "experimental",
        "calibrated": False,
        "backtested": False,
        "probabilistic": False,
        "eligible_for_decision_ranking": False,
        "version": None,
        "reason": "scenario_envelope_not_empirically_calibrated_or_backtested",
    }
