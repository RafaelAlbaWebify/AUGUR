from app.models.profile import LanguageSkill, PersonalProfileResponse
from app.services import language_fit as module
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


def test_language_fit_exposes_esco_occupation_language_evidence(monkeypatch):
    monkeypatch.setattr(
        module,
        "resolve_esco_occupation",
        lambda profession: {
            "status": "matched",
            "selected": {
                "preferred_label": "ICT support technician",
                "match_score": 0.86,
            },
            "candidates": [],
            "threshold": 0.72,
        },
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "language_skill_count": 120,
            "relation_count": 120000,
        },
    )
    monkeypatch.setattr(
        module,
        "occupation_language_skill_rows",
        lambda occupation_label: [
            {
                "skill_uri": "urn:test:language",
                "skill_label": "communicate in English",
                "relation_type": "essential",
            },
            {
                "skill_uri": "urn:test:language-optional",
                "skill_label": "use foreign languages for international trade",
                "relation_type": "optional",
            },
        ],
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="IT support engineer",
        languages=[LanguageSkill(language="English", cefr="B2")],
    )

    result = language_fit(profile, "IRL")

    assert result["status"] == "work_ready_heuristic"
    assert result["work_ready"] is True

    evidence = result["occupation_language_evidence"]
    assert evidence["status"] == "occupation_language_evidence_available"
    assert evidence["occupation_label"] == "ICT support technician"
    assert evidence["dataset_mode"] == "full"
    assert evidence["essential_skill_count"] == 1
    assert evidence["optional_skill_count"] == 1
    assert evidence["evidence_complete"] is True


def test_esco_language_evidence_does_not_create_cefr_readiness(monkeypatch):
    monkeypatch.setattr(
        module,
        "resolve_esco_occupation",
        lambda profession: {
            "status": "matched",
            "selected": {
                "preferred_label": "ICT support technician",
                "match_score": 0.86,
            },
            "candidates": [],
            "threshold": 0.72,
        },
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "language_skill_count": 120,
            "relation_count": 120000,
        },
    )
    monkeypatch.setattr(
        module,
        "occupation_language_skill_rows",
        lambda occupation_label: [
            {
                "skill_uri": "urn:test:language",
                "skill_label": "communicate in English",
                "relation_type": "essential",
            }
        ],
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="IT support engineer",
        languages=[],
    )

    result = language_fit(profile, "IRL")

    assert result["occupation_language_evidence"]["evidence_complete"] is True
    assert result["status"] == "target_language_missing"
    assert result["work_ready"] is False
