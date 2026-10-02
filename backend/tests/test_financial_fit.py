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


def test_financial_fit_exposes_structural_local_income_reference(monkeypatch):
    monkeypatch.setattr(
        module,
        "resolve_esco_occupation",
        lambda profession: {
            "status": "matched",
            "selected": {
                "preferred_label": "ICT support technician",
                "match_score": 0.84,
                "isco_group": "3512",
            },
            "candidates": [],
            "threshold": 0.72,
        },
    )
    monkeypatch.setattr(
        module,
        "latest_labour_earnings",
        lambda country_iso3, isco08: [
            {
                "country_iso3": country_iso3,
                "period": 2022,
                "isco08": isco08,
                "value": 3200.0,
                "unit": "eur_gross_monthly",
                "source_id": "EUROSTAT",
                "dataset_id": "earn_ses22_21",
                "source_updated_at": "2026-02-09",
            }
        ],
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        current_country="ESP",
        profession="IT support engineer",
        monthly_net_income=3000,
        remote_work=False,
    )

    result = module.financial_fit(profile, "PRT")

    assert result["status"] == "local_income_reference_available"
    assert result["reason"] == "net_income_not_modelled"
    assert result["portable_income_analysis"] is None
    reference = result["local_income_reference"]
    assert reference["occupation_label"] == "ICT support technician"
    assert reference["ses_isco_major_group"] == "OC3"
    assert reference["gross_monthly_mean_eur"] == 3200.0
    assert reference["period"] == 2022
    assert reference["dataset_id"] == "earn_ses22_21"


def test_financial_fit_keeps_national_net_benchmark_separate(monkeypatch):
    monkeypatch.setattr(
        module,
        "resolve_esco_occupation",
        lambda profession: {
            "status": "matched",
            "selected": {
                "preferred_label": "ICT support technician",
                "match_score": 0.84,
                "isco_group": "3512",
            },
            "candidates": [],
            "threshold": 0.72,
        },
    )
    monkeypatch.setattr(
        module,
        "latest_labour_earnings",
        lambda country_iso3, isco08: [
            {
                "country_iso3": country_iso3,
                "period": 2022,
                "isco08": isco08,
                "value": 3200.0,
                "unit": "eur_gross_monthly",
                "source_id": "EUROSTAT",
                "dataset_id": "earn_ses22_21",
                "source_updated_at": "2026-02-09",
            }
        ],
    )
    monkeypatch.setattr(
        module,
        "latest_labour_net_earnings_reference",
        lambda country_iso3: {
            "country_iso3": country_iso3,
            "period": 2025,
            "earnings_case": "P1_NCH_AW100",
            "annual_net_eur": 30000.0,
            "source_id": "EUROSTAT",
            "dataset_id": "earn_nt_net",
            "source_updated_at": "2026-09-04",
        },
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        current_country="ESP",
        profession="IT support engineer",
        monthly_net_income=3000,
        remote_work=False,
    )

    result = module.financial_fit(profile, "PRT")

    assert result["status"] == "local_income_reference_available"
    assert result["reason"] == "occupation_specific_net_income_not_modelled"

    gross = result["local_income_reference"]
    net = result["national_net_earnings_reference"]

    assert gross["gross_monthly_mean_eur"] == 3200.0
    assert net["annual_net_eur"] == 30000.0
    assert net["monthly_net_equivalent_eur"] == 2500.0
    assert net["scope"] == "national_average_worker_standard_case"

    assert "estimated_occupation_net" not in result
    assert result["portable_income_analysis"] is None
