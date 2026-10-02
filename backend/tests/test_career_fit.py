from app.models.profile import PersonalProfileResponse
from app.services import career_fit as career_fit_module
from app.services.career_fit import career_fit, classify_occupation, resolve_esco_occupation


def _disable_esco_lookup(monkeypatch):
    monkeypatch.setattr(career_fit_module, "search_occupations", lambda profession, limit=5: [])


def test_esco_resolution_accepts_confident_match(monkeypatch):
    monkeypatch.setattr(
        career_fit_module,
        "search_occupations",
        lambda profession, limit=5: [
            {
                "concept_uri": "urn:test:ict-support",
                "preferred_label": "ICT support technician",
                "code": "3512",
                "isco_group": "3512",
                "dataset_version": "test",
                "source_mode": "full",
                "match_score": 0.81,
                "match_method": "token_overlap",
            }
        ],
    )

    result = resolve_esco_occupation("IT support engineer")

    assert result["status"] == "matched"
    assert result["selected"]["preferred_label"] == "ICT support technician"
    assert result["selected"]["match_score"] == 0.81


def test_esco_resolution_refuses_weak_match(monkeypatch):
    monkeypatch.setattr(
        career_fit_module,
        "search_occupations",
        lambda profession, limit=5: [
            {
                "concept_uri": "urn:test:weak",
                "preferred_label": "engineering technician",
                "code": None,
                "isco_group": "3119",
                "dataset_version": "test",
                "source_mode": "full",
                "match_score": 0.51,
                "match_method": "token_overlap",
            }
        ],
    )

    result = resolve_esco_occupation("IT support engineer")

    assert result["status"] == "no_confident_match"
    assert result["selected"] is None
    assert result["candidates"][0]["match_score"] == 0.51


def test_missing_profession_is_not_mapped():
    result = classify_occupation(None)
    assert result["status"] == "profession_missing"
    assert result["occupation_group"] is None


def test_software_profession_maps_to_ict():
    result = classify_occupation("Software developer")
    assert result["status"] == "mapped"
    assert result["occupation_group"] == "ict_professionals"


def test_ireland_ict_maps_to_shortage_signal(monkeypatch):
    _disable_esco_lookup(monkeypatch)
    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Software developer",
    )

    result = career_fit(profile, "IRL")

    assert result["status"] == "evidence_available"
    assert result["market_signal"] == "shortage"
    assert result["occupation"]["occupation_group"] == "ict_professionals"
    assert result["source"]["label"].startswith("EURES")
    assert result["evidence_complete"] is False
    assert result["skill_match"]["status"] == "occupation_not_mapped_to_esco"


def test_portugal_ict_maps_to_shortage_signal(monkeypatch):
    _disable_esco_lookup(monkeypatch)
    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Cybersecurity analyst",
    )

    result = career_fit(profile, "PRT")

    assert result["market_signal"] == "shortage"


def test_spain_engineering_maps_to_surplus_signal(monkeypatch):
    _disable_esco_lookup(monkeypatch)
    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Mechanical engineer",
    )

    result = career_fit(profile, "ESP")

    assert result["market_signal"] == "surplus"


def test_unmapped_profession_does_not_infer_demand(monkeypatch):
    _disable_esco_lookup(monkeypatch)
    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Specialist role xyz",
    )

    result = career_fit(profile, "IRL")

    assert result["status"] == "occupation_unmapped"
    assert result["market_signal"] is None
