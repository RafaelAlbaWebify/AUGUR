from app.models.profile import PersonalProfileResponse
from app.services import career_fit as career_fit_module
from app.services.career_fit import (
    COUNTRY_EVIDENCE,
    EURES_EVIDENCE_METADATA,
    career_fit,
    classify_occupation,
    resolve_esco_occupation,
    career_market_evidence_status,
)


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


def _mock_full_esco_career(
    monkeypatch,
    market_country_profession="IT support engineer",
    coverage=1.0,
    isco_group="2522",
    vacancy_rate=4.2,
):
    monkeypatch.setattr(
        career_fit_module,
        "search_occupations",
        lambda profession, limit=5: [
            {
                "concept_uri": "urn:test:ict-support",
                "preferred_label": (
                    "ICT support technician"
                    if isco_group.startswith("35")
                    else "ICT professional"
                    if isco_group.startswith("25")
                    else "engineering professional"
                ),
                "code": isco_group,
                "isco_group": isco_group,
                "dataset_version": "1.2.1",
                "source_mode": "full",
                "match_score": 0.86,
                "match_method": "token_overlap",
            }
        ],
    )

    monkeypatch.setattr(
        career_fit_module,
        "latest_labour_job_vacancy_rate",
        lambda country_iso3, isco08: (
            {
                "country_iso3": country_iso3,
                "period": "2024",
                "isco08": isco08,
                "vacancy_rate_pct": vacancy_rate,
                "nace_scope": None,
                "source_id": "EUROSTAT",
                "dataset_id": "jvs_a_isco3_r1",
                "source_updated_at": "2025-12-10",
            }
            if vacancy_rate is not None
            else None
        ),
    )

    monkeypatch.setattr(
        career_fit_module,
        "latest_labour_occupation_outlook",
        lambda country_iso3, isco08, scenario="Aligned_forecast_Ameco": [],
    )

    monkeypatch.setattr(
        career_fit_module,
        "latest_labour_oja_imbalance_eu27",
        lambda isco08: None,
    )

    total = 4
    matched = int(total * coverage)
    monkeypatch.setattr(
        career_fit_module,
        "match_profile_skills",
        lambda occupation_label, profile_skills: {
            "status": "matched",
            "dataset_mode": "full",
            "dataset_version": "1.2.1",
            "occupation_label": occupation_label,
            "matched_skills": [],
            "missing_skills": [],
            "essential_skill_count": total,
            "essential_skills_matched": matched,
            "coverage": matched / total,
            "evidence_complete": True,
        },
    )


def test_career_viability_evidence_requires_shortage_and_complete_essential_skills(monkeypatch):
    _mock_full_esco_career(monkeypatch, coverage=1.0)

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="IT support engineer",
        skills=["Windows", "networking", "ticketing", "troubleshooting"],
    )

    result = career_fit(profile, "IRL")

    assert result["market_signal"] == "shortage"
    assert result["skill_evidence_complete"] is True
    assert result["market_evidence_complete"] is True
    assert result["evidence_complete"] is True
    assert result["profile_skill_coverage_complete"] is True
    assert result["market_signal_supports_viability"] is True
    assert result["viability_evidence_ready"] is True


def test_career_viability_evidence_blocks_incomplete_essential_skill_coverage(monkeypatch):
    _mock_full_esco_career(monkeypatch, coverage=0.5)

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="IT support engineer",
        skills=["Windows"],
    )

    result = career_fit(profile, "IRL")

    assert result["market_signal"] == "shortage"
    assert result["evidence_complete"] is True
    assert result["profile_skill_coverage_complete"] is False
    assert result["viability_evidence_ready"] is False


def test_career_viability_evidence_does_not_treat_surplus_as_supportive(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="2144",
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Mechanical engineer",
        skills=["Windows", "networking", "ticketing", "troubleshooting"],
    )

    result = career_fit(profile, "ESP")

    assert result["market_signal"] == "surplus"
    assert result["profile_skill_coverage_complete"] is True
    assert result["market_signal_supports_viability"] is False
    assert result["viability_evidence_ready"] is False


def test_eures_market_evidence_is_versioned_outside_service_logic():
    assert EURES_EVIDENCE_METADATA["evidence_id"] == "eures_market_evidence_composite"
    assert EURES_EVIDENCE_METADATA["rule_version"] == "EURES_MARKET_COMPOSITE_2026_10"
    assert EURES_EVIDENCE_METADATA["broad_evidence"]["evidence_id"] == "eures_country_lmi_2024_conditions"
    assert EURES_EVIDENCE_METADATA["broad_evidence"]["conditions_year"] == 2024
    assert EURES_EVIDENCE_METADATA["unit_group_evidence"]["evidence_id"] == "eures_shortages_surpluses_2025_annex"
    assert EURES_EVIDENCE_METADATA["unit_group_evidence"]["conditions_year"] == 2025
    assert EURES_EVIDENCE_METADATA["unit_group_evidence"]["report_year"] == 2026
    assert set(COUNTRY_EVIDENCE) == {"ESP", "PRT", "IRL"}
    assert "ict_professionals" in COUNTRY_EVIDENCE["IRL"]["shortage_groups"]
    assert isinstance(COUNTRY_EVIDENCE["ESP"]["surplus_groups"], set)
    assert COUNTRY_EVIDENCE["ESP"]["eures_country_code"] == "ES"
    assert COUNTRY_EVIDENCE["PRT"]["eures_country_code"] == "PT"
    assert COUNTRY_EVIDENCE["IRL"]["eures_country_code"] == "IE"


def test_isco_35_support_technician_does_not_inherit_isco_25_shortage(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="3512",
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="IT support engineer",
        skills=["Windows", "networking", "ticketing", "troubleshooting"],
    )

    result = career_fit(profile, "IRL")

    assert result["occupation"]["mapping_method"] == "esco_isco_submajor"
    assert result["occupation"]["isco_submajor"] == "35"
    assert result["occupation"]["occupation_group"] == "information_communications_technicians"
    assert result["market_signal"] == "not_classified_as_shortage_or_surplus"
    assert result["profile_skill_coverage_complete"] is True
    assert result["market_signal_supports_viability"] is False
    assert result["viability_evidence_ready"] is False


def test_isco_25_ict_professional_can_use_ict_professional_shortage(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="2522",
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Systems administrator",
        skills=["Windows", "networking", "ticketing", "troubleshooting"],
    )

    result = career_fit(profile, "IRL")

    assert result["occupation"]["isco_submajor"] == "25"
    assert result["occupation"]["occupation_group"] == "ict_professionals"
    assert result["market_signal"] == "shortage"
    assert result["viability_evidence_ready"] is True


def test_unit_group_surplus_overrides_broad_ict_shortage(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="2511",
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Systems analyst",
        skills=["analysis", "systems", "requirements", "documentation"],
    )

    result = career_fit(profile, "PRT")

    assert result["occupation"]["occupation_group"] == "ict_professionals"
    assert result["market_signal_scope"] == "isco_unit_group"
    assert result["market_signal_isco"] == "2511"
    assert result["market_signal"] == "surplus"
    assert result["market_signal_supports_viability"] is False
    assert result["viability_evidence_ready"] is False


def test_unit_group_unclassified_overrides_broad_ict_shortage(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="2522",
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Systems administrator",
        skills=["Windows", "networking", "ticketing", "troubleshooting"],
    )

    result = career_fit(profile, "PRT")

    assert result["occupation"]["occupation_group"] == "ict_professionals"
    assert result["market_signal_scope"] == "isco_unit_group"
    assert result["market_signal_isco"] == "2522"
    assert result["market_signal"] == "not_classified_as_shortage_or_surplus"
    assert result["viability_evidence_ready"] is False


def test_verified_ict_unit_group_manifest_has_expected_country_signals():
    unit_signals = EURES_EVIDENCE_METADATA["unit_group_signals"]

    assert unit_signals["3512"]["occupation_label"] == "Information and communications technology user support technicians"
    assert "ES" not in unit_signals["3512"]["surplus_countries"]
    assert "PT" in unit_signals["3512"]["surplus_countries"]
    assert "IE" not in unit_signals["3512"]["shortage_countries"]
    assert "IE" not in unit_signals["3512"]["surplus_countries"]

    assert "IE" in unit_signals["2522"]["shortage_countries"]
    assert "PT" not in unit_signals["2522"]["shortage_countries"]
    assert "PT" not in unit_signals["2522"]["surplus_countries"]

    assert "PT" in unit_signals["2511"]["surplus_countries"]
    assert "IE" in unit_signals["2512"]["shortage_countries"]
    assert "PT" in unit_signals["2512"]["shortage_countries"]
    assert "PT" in unit_signals["2513"]["surplus_countries"]
    assert "ES" in unit_signals["2521"]["surplus_countries"]
    assert "IE" in unit_signals["2529"]["shortage_countries"]
    assert "PT" in unit_signals["2529"]["shortage_countries"]
    assert "ES" in unit_signals["3511"]["shortage_countries"]


def test_broad_shortage_does_not_count_as_complete_market_evidence(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="2211",
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="General practitioner",
        skills=["diagnosis", "patient care", "treatment", "documentation"],
    )

    result = career_fit(profile, "PRT")

    assert result["occupation"]["occupation_group"] == "health_professionals"
    assert result["market_signal_scope"] == "broad_occupation_group"
    assert result["market_signal"] == "shortage"
    assert result["skill_evidence_complete"] is True
    assert result["market_evidence_complete"] is False
    assert result["evidence_complete"] is False
    assert result["market_signal_supports_viability"] is False
    assert result["viability_evidence_ready"] is False
    assert result["source"]["evidence_id"] == "eures_country_lmi_2024_conditions"
    assert result["source"]["conditions_year"] == 2024
    assert result["source"]["scope"] == "broad_occupation_group"


def test_vacancy_rate_context_does_not_override_market_gate(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="3512",
        vacancy_rate=8.7,
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="IT support engineer",
        skills=["Windows", "networking", "ticketing", "troubleshooting"],
    )

    result = career_fit(profile, "ESP")

    demand = result["vacancy_demand_evidence"]
    assert demand["status"] == "available"
    assert demand["isco_major"] == "OC3"
    assert demand["isco_3digit"] == "OC351"
    assert demand["granularity"] == "isco_3digit"
    assert demand["vacancy_rate_pct"] == 8.7
    assert demand["period"] == "2024"
    assert demand["dataset_id"] == "jvs_a_isco3_r1"
    assert demand["role"] == "context_only"

    assert result["market_signal"] == "not_classified_as_shortage_or_surplus"
    assert result["market_evidence_complete"] is True
    assert result["market_signal_supports_viability"] is False
    assert result["viability_evidence_ready"] is False


def test_unavailable_vacancy_source_does_not_make_complete_eures_evidence_partial(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="2522",
        vacancy_rate=None,
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Systems administrator",
        skills=["Windows", "networking", "ticketing", "troubleshooting"],
    )

    result = career_fit(profile, "IRL")

    assert result["vacancy_demand_evidence"]["status"] == "source_coverage_unavailable"
    assert result["vacancy_demand_evidence"]["dataset_id"] == "jvs_a_isco3_r1"
    assert result["market_signal"] == "shortage"
    assert result["market_evidence_complete"] is True
    assert result["evidence_complete"] is True
    assert result["viability_evidence_ready"] is True


def test_career_market_evidence_status_is_explicitly_partial():
    result = career_market_evidence_status()

    assert result["supported_countries"] == ["ESP", "IRL", "PRT"]
    assert result["broad_country_count"] == 3
    assert result["unit_group_count"] >= 13
    assert result["coverage_scope"] == "partial_unit_group_coverage"
    assert result["full_occupation_coverage"] is False


def test_latest_unit_group_source_provenance_is_returned(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="2512",
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Software developer",
        skills=["Python", "software design", "testing", "documentation"],
    )

    result = career_fit(profile, "IRL")

    assert result["market_signal"] == "shortage"
    assert result["market_signal_scope"] == "isco_unit_group"
    assert result["market_signal_isco"] == "2512"
    assert result["source"]["evidence_id"] == "eures_shortages_surpluses_2025_annex"
    assert result["source"]["rule_version"] == "EURES_SHORTAGES_SURPLUSES_2025_ANNEX"
    assert result["source"]["report_year"] == 2026
    assert result["source"]["conditions_year"] == 2025
    assert result["source"]["scope"] == "isco_unit_group"
    assert result["rule_version"] == "EURES_SHORTAGES_SURPLUSES_2025_ANNEX"


def test_latest_annex_changes_3512_spain_from_old_surplus_to_unclassified(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="3512",
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="IT support engineer",
        skills=["Windows", "networking", "ticketing", "troubleshooting"],
    )

    result = career_fit(profile, "ESP")

    assert result["market_signal"] == "not_classified_as_shortage_or_surplus"
    assert result["market_signal_scope"] == "isco_unit_group"
    assert result["market_evidence_complete"] is True
    assert result["market_signal_supports_viability"] is False


def test_latest_annex_3512_portugal_remains_surplus(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="3512",
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="IT support engineer",
        skills=["Windows", "networking", "ticketing", "troubleshooting"],
    )

    result = career_fit(profile, "PRT")

    assert result["market_signal"] == "surplus"
    assert result["market_signal_scope"] == "isco_unit_group"
    assert result["market_signal_supports_viability"] is False


def test_mixed_unit_group_signal_is_not_supportive(monkeypatch):
    original = career_fit_module.COUNTRY_EVIDENCE["IRL"]["eures_country_code"]
    monkeypatch.setitem(
        career_fit_module.COUNTRY_EVIDENCE["IRL"],
        "eures_country_code",
        "BE",
    )
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="2511",
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        profession="Systems analyst",
        skills=["analysis", "systems", "requirements", "documentation"],
    )

    result = career_fit(profile, "IRL")

    assert original == "IE"
    assert result["market_signal"] == "mixed_shortage_and_surplus"
    assert result["market_evidence_complete"] is True
    assert result["market_signal_supports_viability"] is False
    assert result["viability_evidence_ready"] is False


def test_vacancy_source_coverage_unavailable_is_distinct_from_missing_evidence(monkeypatch):
    _mock_full_esco_career(
        monkeypatch,
        coverage=1.0,
        isco_group="2522",
        vacancy_rate=None,
    )

    evidence = career_fit_module.occupation_vacancy_demand_evidence(
        "IRL",
        {
            "selected": {
                "isco_group": "2522",
                "code": "2522",
            }
        },
    )

    assert evidence["status"] == "source_coverage_unavailable"
    assert evidence["dataset_id"] == "jvs_a_isco3_r1"
    assert evidence["supported_countries"] == ["ESP", "PRT"]
    assert evidence["isco_3digit"] == "OC252"
    assert "zero vacancy demand" in evidence["notes"][1]


def test_vacancy_rate_prefers_isco3_before_major_fallback(monkeypatch):
    requested = []

    monkeypatch.setattr(
        career_fit_module,
        "latest_labour_job_vacancy_rate",
        lambda country_iso3, isco08: (
            requested.append(isco08)
            or ({
                "country_iso3": country_iso3,
                "period": "2024",
                "isco08": isco08,
                "vacancy_rate_pct": 4.6,
                "nace_scope": None,
                "source_id": "EUROSTAT",
                "dataset_id": "jvs_a_isco3_r1",
                "source_updated_at": "2025-12-10",
            } if isco08 == "OC351" else None)
        ),
    )

    evidence = career_fit_module.occupation_vacancy_demand_evidence(
        "ESP",
        {
            "selected": {
                "isco_group": "3512",
                "code": "3512",
            }
        },
    )

    assert requested == ["OC351"]
    assert evidence["status"] == "available"
    assert evidence["isco_3digit"] == "OC351"
    assert evidence["granularity"] == "isco_3digit"


def test_stas_outlook_prefers_isco2_and_is_context_only(monkeypatch):
    requested = []

    monkeypatch.setattr(
        career_fit_module,
        "latest_labour_occupation_outlook",
        lambda country_iso3, isco08, scenario="Aligned_forecast_Ameco": (
            requested.append(isco08)
            or (
                [
                    {
                        "country_iso3": country_iso3,
                        "period": 2026,
                        "isco08": "25",
                        "isco_level": 2,
                        "occupation_label": "Information and communications technology professionals",
                        "scenario": scenario,
                        "employment_level_thousands": 400.0,
                        "employment_growth_pct": 1.2,
                        "source_id": "CEDEFOP",
                        "dataset_id": "CEDEFOP_STAS",
                        "release_version": "2026-08",
                        "retrieved_at": None,
                        "source_updated_at": "2026-08",
                    },
                    {
                        "country_iso3": country_iso3,
                        "period": 2027,
                        "isco08": "25",
                        "isco_level": 2,
                        "occupation_label": "Information and communications technology professionals",
                        "scenario": scenario,
                        "employment_level_thousands": 410.0,
                        "employment_growth_pct": 2.5,
                        "source_id": "CEDEFOP",
                        "dataset_id": "CEDEFOP_STAS",
                        "release_version": "2026-08",
                        "retrieved_at": None,
                        "source_updated_at": "2026-08",
                    },
                ]
                if isco08 == "25"
                else []
            )
        ),
    )

    evidence = career_fit_module.occupation_outlook_evidence(
        "ESP",
        {"selected": {"isco_group": "2522", "code": "2522"}},
    )

    assert requested == ["25"]
    assert evidence["status"] == "available"
    assert evidence["granularity"] == "isco_2digit"
    assert evidence["isco08"] == "25"
    assert evidence["horizons"][1]["period"] == 2027
    assert evidence["horizons"][1]["employment_growth_pct"] == 2.5
    assert evidence["role"] == "context_only"


def test_stas_outlook_falls_back_to_isco1(monkeypatch):
    requested = []

    def fake_outlook(country_iso3, isco08, scenario="Aligned_forecast_Ameco"):
        requested.append(isco08)
        if isco08 == "2":
            return [{
                "country_iso3": country_iso3,
                "period": 2027,
                "isco08": "2",
                "isco_level": 1,
                "occupation_label": "Professionals",
                "scenario": scenario,
                "employment_level_thousands": 1000.0,
                "employment_growth_pct": 1.5,
                "source_id": "CEDEFOP",
                "dataset_id": "CEDEFOP_STAS",
                "release_version": "2026-08",
                "retrieved_at": None,
                "source_updated_at": "2026-08",
            }]
        return []

    monkeypatch.setattr(
        career_fit_module,
        "latest_labour_occupation_outlook",
        fake_outlook,
    )

    evidence = career_fit_module.occupation_outlook_evidence(
        "ESP",
        {"selected": {"isco_group": "2522", "code": "2522"}},
    )

    assert requested == ["25", "2"]
    assert evidence["status"] == "available"
    assert evidence["granularity"] == "isco_1digit"
    assert evidence["isco08"] == "2"


def test_eu27_oja_imbalance_is_context_only(monkeypatch):
    monkeypatch.setattr(
        career_fit_module,
        "latest_labour_oja_imbalance_eu27",
        lambda isco08: {
            "isco08": isco08,
            "major_group_label": "2 Professionals",
            "occupation_label": "Systems administrators",
            "score": 0.625,
            "source_id": "CEDEFOP",
            "dataset_id": "CEDEFOP_OJA_IMBALANCE",
            "release_version": "2026-05",
            "retrieved_at": None,
            "source_updated_at": "2026-05",
        },
    )

    evidence = career_fit_module.eu27_oja_imbalance_evidence(
        {"selected": {"isco_group": "2522", "code": "2522"}}
    )

    assert evidence["status"] == "available"
    assert evidence["isco08"] == "2522"
    assert evidence["score"] == 0.625
    assert evidence["geographic_scope"] == "EU27"
    assert evidence["role"] == "context_only"
    assert "not country-specific" in evidence["notes"][2]
