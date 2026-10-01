from app.models.profile import PersonalProfileResponse
from app.services.career_fit import career_fit, classify_occupation


def test_missing_profession_is_not_mapped():
    result = classify_occupation(None)
    assert result["status"] == "profession_missing"
    assert result["occupation_group"] is None


def test_software_profession_maps_to_ict():
    result = classify_occupation("Software developer")
    assert result["status"] == "mapped"
    assert result["occupation_group"] == "ict_professionals"


def test_ireland_ict_maps_to_shortage_signal():
    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Software developer",
    )

    result = career_fit(profile, "IRL")

    assert result["status"] == "evidence_available"
    assert result["market_signal"] == "shortage"
    assert result["occupation"]["occupation_group"] == "ict_professionals"
    assert result["source"]["label"].startswith("EURES")


def test_portugal_ict_maps_to_shortage_signal():
    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Cybersecurity analyst",
    )

    result = career_fit(profile, "PRT")

    assert result["market_signal"] == "shortage"


def test_spain_engineering_maps_to_surplus_signal():
    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Mechanical engineer",
    )

    result = career_fit(profile, "ESP")

    assert result["market_signal"] == "surplus"


def test_unmapped_profession_does_not_infer_demand():
    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Specialist role xyz",
    )

    result = career_fit(profile, "IRL")

    assert result["status"] == "occupation_unmapped"
    assert result["market_signal"] is None
