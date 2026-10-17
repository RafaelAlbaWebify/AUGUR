"""Scenario empty horizon is intentional and must not be replaced with defaults."""
from unittest.mock import patch
from app.services.scenarios import country_scenarios, DEFAULT_HORIZONS


def test_explicit_empty_horizons_are_preserved():
    with patch("app.services.scenarios.future_trajectory", return_value=[]) as read:
        result=country_scenarios("ESP", horizons=[])
    read.assert_called_once_with("ESP", [])
    assert result["horizons"]==[]
    assert result["indicators"]==[]


def test_omitted_horizons_use_documented_defaults():
    with patch("app.services.scenarios.future_trajectory", return_value=[]) as read:
        result=country_scenarios("ESP")
    read.assert_called_once_with("ESP", DEFAULT_HORIZONS)
    assert result["horizons"]==DEFAULT_HORIZONS
