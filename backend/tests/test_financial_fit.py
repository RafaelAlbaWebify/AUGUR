from app.models.profile import PersonalProfileResponse
from app.services import financial_fit as module


def test_financial_fit_requires_current_country():
    profile = PersonalProfileResponse(
        profile_id="default",
        monthly_net_income=3000,
        remote_work=True,
    )

    result = module.financial_fit(profile, "PRT")

    assert result["status"] == "insufficient_profile"
    assert result["reason"] == "current_country_missing"


def test_financial_fit_does_not_assume_income_portability():
    profile = PersonalProfileResponse(
        profile_id="default",
        current_country="ESP",
        monthly_net_income=3000,
        remote_work=False,
    )

    result = module.financial_fit(profile, "PRT")

    assert result["status"] == "local_income_unknown"
    assert result["portable_income_analysis"] is None


def test_financial_fit_uses_relative_price_levels_for_remote_income(monkeypatch):
    price_levels = {
        "ESP": {
            "indicator_id": "household_price_level_index",
            "value": 95.0,
            "period": 2024,
            "source_id": "EUROSTAT",
        },
        "IRL": {
            "indicator_id": "household_price_level_index",
            "value": 138.0,
            "period": 2024,
            "source_id": "EUROSTAT",
        },
    }

    monkeypatch.setattr(
        module,
        "_latest_price_level",
        lambda country_iso3: price_levels.get(country_iso3),
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        current_country="ESP",
        monthly_net_income=3000,
        remote_work=True,
    )

    result = module.financial_fit(profile, "IRL")

    assert result["status"] == "portable_income_comparable"
    analysis = result["portable_income_analysis"]
    assert round(analysis["relative_cost_factor"], 3) == round(138 / 95, 3)
    assert analysis["origin_equivalent_purchasing_power"] < 3000
    assert analysis["purchasing_power_change_pct"] < 0
    assert analysis["source_id"] == "EUROSTAT"
