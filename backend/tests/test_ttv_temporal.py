from app.models.profile import LanguageSkill, PersonalProfileResponse
from app.services import ttv_temporal as module
from app.services.ttv_temporal import temporal_evidence_graph


def _legal_ready():
    return {"status": "eu_free_movement_framework"}


def _language_b1():
    return {
        "status": "language_gap",
        "work_ready": False,
        "matches": [
            {
                "language": "English",
                "declared_cefr": "B1",
                "meets_work_ready_heuristic": False,
            }
        ],
    }


def _career_ready():
    return {
        "status": "evidence_available",
        "viability_evidence_ready": True,
        "evidence_complete": True,
        "profile_skill_coverage_complete": True,
        "market_signal_supports_viability": True,
    }


def _financial_ready():
    return {
        "status": "portable_income_comparable",
        "reason": None,
    }


def test_temporal_graph_converts_b1_to_b2_hours_using_user_study_intensity():
    profile = PersonalProfileResponse(
        profile_id="default",
        remote_work=True,
        preferences={"language_study_hours_per_week": 10},
    )

    result = temporal_evidence_graph(
        profile,
        "IRL",
        _legal_ready(),
        _language_b1(),
        _career_ready(),
        _financial_ready(),
    )

    language = result["stages"]["language"]

    assert language["status"] == "available"
    assert language["current_cefr"] == "B1"
    assert language["target_cefr"] == "B2"
    assert language["guided_hours_min"] == 100
    assert language["guided_hours_max"] == 250
    assert language["weekly_study_hours"] == 10
    assert language["weeks_min"] == 10
    assert language["weeks_max"] == 25

    assert result["calendar_ready"] is True
    assert result["candidate_range"] == {
        "weeks_min": 10,
        "weeks_max": 25,
        "composition": "parallel_max",
    }


def test_temporal_graph_withholds_calendar_when_study_intensity_is_missing():
    profile = PersonalProfileResponse(
        profile_id="default",
        remote_work=True,
    )

    result = temporal_evidence_graph(
        profile,
        "IRL",
        _legal_ready(),
        _language_b1(),
        _career_ready(),
        _financial_ready(),
    )

    language = result["stages"]["language"]

    assert language["status"] == "guided_hours_available_calendar_missing"
    assert language["guided_hours_min"] == 100
    assert language["guided_hours_max"] == 250
    assert language["weeks_min"] is None
    assert language["weeks_max"] is None
    assert result["calendar_ready"] is False
    assert result["candidate_range"] is None
    assert result["unavailable_stages"] == ["language"]


def test_temporal_graph_withholds_local_employment_when_baseline_missing(monkeypatch):
    monkeypatch.setattr(module, "latest_labour_job_transition", lambda country_iso3: None)
    profile = PersonalProfileResponse(
        profile_id="default",
        remote_work=False,
        preferences={"language_study_hours_per_week": 10},
    )

    result = temporal_evidence_graph(
        profile,
        "IRL",
        _legal_ready(),
        {
            "status": "work_ready_heuristic",
            "work_ready": True,
            "matches": [
                {
                    "language": "English",
                    "declared_cefr": "B2",
                    "meets_work_ready_heuristic": True,
                }
            ],
        },
        _career_ready(),
        {
            "status": "local_income_reference_available",
            "reason": "net_income_not_modelled",
        },
    )

    assert result["stages"]["employment"]["status"] == "unavailable"
    assert result["stages"]["financial"]["status"] == "unavailable"
    assert set(result["unavailable_stages"]) == {"financial", "employment"}
    assert result["calendar_ready"] is False


def test_temporal_graph_does_not_assume_beginner_level_when_target_language_missing():
    profile = PersonalProfileResponse(
        profile_id="default",
        remote_work=True,
        preferences={"language_study_hours_per_week": 10},
    )

    result = temporal_evidence_graph(
        profile,
        "IRL",
        _legal_ready(),
        {
            "status": "target_language_missing",
            "work_ready": False,
            "matches": [
                {
                    "language": "English",
                    "declared_cefr": None,
                    "meets_work_ready_heuristic": False,
                }
            ],
        },
        _career_ready(),
        _financial_ready(),
    )

    language = result["stages"]["language"]

    assert language["status"] == "unavailable"
    assert language["reason"] == "target_language_cefr_required_for_temporal_estimate"
    assert language["current_cefr"] is None


def test_local_employment_uses_experimental_country_transition_baseline(monkeypatch):
    monkeypatch.setattr(
        module,
        "latest_labour_job_transition",
        lambda country_iso3: {
            "country_iso3": country_iso3,
            "period": 2025,
            "age_group": "Y15-74",
            "duration_group": "TOTAL",
            "probability_pct": 25.0,
            "source_id": "EUROSTAT",
            "dataset_id": "lfsi_long_e01",
        },
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        remote_work=False,
        preferences={"language_study_hours_per_week": 10},
    )

    result = temporal_evidence_graph(
        profile,
        "IRL",
        _legal_ready(),
        {
            "status": "work_ready_heuristic",
            "work_ready": True,
            "matches": [
                {
                    "language": "English",
                    "declared_cefr": "B2",
                    "meets_work_ready_heuristic": True,
                }
            ],
        },
        _career_ready(),
        {
            "status": "local_income_reference_available",
            "reason": "net_income_not_modelled",
        },
    )

    employment = result["stages"]["employment"]

    assert employment["status"] == "available"
    assert employment["quarterly_transition_probability_pct"] == 25.0
    assert employment["weeks_min"] == 39
    assert employment["weeks_max"] == 78
    assert employment["range_definition"]["lower_cumulative_probability"] == 0.50
    assert employment["range_definition"]["upper_cumulative_probability"] == 0.80
    assert employment["range_definition"]["constant_quarterly_hazard_assumption"] is True

    assert result["stages"]["financial"]["status"] == "unavailable"
    assert result["calendar_ready"] is False
    assert result["candidate_range"] is None
