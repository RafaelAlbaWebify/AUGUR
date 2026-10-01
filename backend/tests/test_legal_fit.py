from app.models.profile import PersonalProfileResponse
from app.services.legal_fit import legal_fit


def test_legal_fit_requires_current_country():
    profile = PersonalProfileResponse(
        profile_id="default",
        citizenships=["ESP"],
    )

    result = legal_fit(profile, "PRT")

    assert result["status"] == "insufficient_profile"


def test_legal_fit_detects_domestic_case():
    profile = PersonalProfileResponse(
        profile_id="default",
        current_country="ESP",
        citizenships=["ESP"],
    )

    result = legal_fit(profile, "ESP")

    assert result["status"] == "domestic"
    assert result["framework"] == "domestic_rules"


def test_eu_citizen_gets_free_movement_framework_for_eu_target():
    profile = PersonalProfileResponse(
        profile_id="default",
        current_country="ESP",
        citizenships=["ESP"],
    )

    result = legal_fit(profile, "IRL")

    assert result["status"] == "eu_free_movement_framework"
    assert result["work_permit_required"] is False
    assert result["short_stay"]["up_to_months"] == 3
    assert result["long_stay"]["registration_may_be_required"] is True
    assert result["sources"]


def test_non_eu_citizenship_does_not_get_guessed_eligibility():
    profile = PersonalProfileResponse(
        profile_id="default",
        current_country="ESP",
        citizenships=["USA"],
    )

    result = legal_fit(profile, "PRT")

    assert result["status"] == "country_specific_rules_required"
    assert result["work_permit_required"] is None
