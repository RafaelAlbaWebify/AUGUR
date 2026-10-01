from app.models.profile import LanguageSkill, PersonalProfileResponse
from app.services.profile_readiness import profile_readiness


def test_empty_profile_reports_missing_fit_inputs():
    result = profile_readiness(
        PersonalProfileResponse(profile_id="default")
    )

    assert result["ready_module_count"] == 0
    assert "citizenships" in result["modules"]["legal_fit"]["missing_fields"]
    assert "profession" in result["modules"]["career_fit"]["missing_fields"]
    assert "languages" in result["modules"]["language_fit"]["missing_fields"]


def test_complete_profile_marks_dependency_modules_ready():
    profile = PersonalProfileResponse(
        profile_id="default",
        age=40,
        current_country="ESP",
        citizenships=["ESP"],
        profession="Systems engineer",
        skills=["Python"],
        languages=[LanguageSkill(language="English", cefr="B2")],
        household_size=2,
        monthly_net_income=3000,
        liquid_savings=20000,
        remote_work=True,
    )

    result = profile_readiness(profile)

    assert result["ready_module_count"] == 4
    assert all(item["ready"] for item in result["modules"].values())
