from app.models.profile import LanguageSkill, PersonalProfileResponse
from app.services import ttv as module


def test_ttv_empty_profile_reports_blockers():
    profile = PersonalProfileResponse(profile_id="default")

    result = module.ttv_status(profile, "IRL")

    assert result["time_estimate"] is None
    assert result["ready_for_time_estimate"] is False
    assert "legal_fit" in result["blocked_by"]
    assert "language_fit" in result["blocked_by"]
    assert "career_fit" in result["blocked_by"]


def test_ttv_keeps_time_estimate_blocked_until_all_dependencies_are_viable(monkeypatch):
    monkeypatch.setattr(
        module,
        "legal_fit",
        lambda profile, target: {
            "status": "eu_free_movement_framework",
        },
    )
    monkeypatch.setattr(
        module,
        "financial_fit",
        lambda profile, target: {
            "status": "portable_income_comparable",
        },
    )
    monkeypatch.setattr(
        module,
        "language_fit",
        lambda profile, target: {
            "status": "work_ready_heuristic",
            "work_ready": True,
        },
    )
    monkeypatch.setattr(
        module,
        "career_fit",
        lambda profile, target: {
            "status": "evidence_available",
            "market_signal": "shortage",
        },
    )

    profile = PersonalProfileResponse(
        profile_id="default",
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

    result = module.ttv_status(profile, "IRL")

    assert result["blocked_by"] == []
    assert result["ready_for_time_estimate"] is True
    assert result["time_estimate"] is None
    assert result["stages"]["language_fit"]["evidence_state"] == "implemented"
    assert result["stages"]["career_fit"]["evidence_state"] == "implemented"
