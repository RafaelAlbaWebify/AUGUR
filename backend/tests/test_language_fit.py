from app.models.profile import LanguageSkill, PersonalProfileResponse
from app.services.language_fit import language_fit


def test_missing_target_language_reports_gap():
    profile = PersonalProfileResponse(
        profile_id="default",
        languages=[LanguageSkill(language="Spanish", cefr="C2")],
    )

    result = language_fit(profile, "IRL")

    assert result["status"] == "target_language_missing"
    assert result["work_ready"] is False
    assert result["target_languages"] == ["English"]


def test_b2_target_language_meets_work_ready_heuristic():
    profile = PersonalProfileResponse(
        profile_id="default",
        languages=[LanguageSkill(language="English", cefr="B2")],
    )

    result = language_fit(profile, "IRL")

    assert result["status"] == "work_ready_heuristic"
    assert result["work_ready"] is True
    assert result["work_ready_threshold"] == "B2"


def test_b1_target_language_reports_language_gap():
    profile = PersonalProfileResponse(
        profile_id="default",
        languages=[LanguageSkill(language="Portuguese", cefr="B1")],
    )

    result = language_fit(profile, "PRT")

    assert result["status"] == "language_gap"
    assert result["work_ready"] is False


def test_declared_language_without_cefr_requests_level():
    profile = PersonalProfileResponse(
        profile_id="default",
        languages=[LanguageSkill(language="Spanish", cefr=None)],
    )

    result = language_fit(profile, "ESP")

    assert result["status"] == "cefr_missing"
    assert result["work_ready"] is False
