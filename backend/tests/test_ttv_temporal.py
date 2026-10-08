from app.models.profile import LanguageSkill, PersonalProfileResponse
from app.services import ttv_temporal as module
from app.services.ttv_temporal import (
    compose_temporal_stages,
    temporal_evidence_graph,
    temporal_model_validation_status,
)


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
        "composition": "critical_path_v1",
        "stage_groups": {
            "preparation_parallel": ["legal", "language", "skills"],
            "employment_after_preparation": ["employment"],
            "financial_after_employment": ["financial"],
        },
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
    monkeypatch.setattr(module, "latest_labour_job_transition", lambda country_iso3, age_group="Y15-74", duration_group="TOTAL": None)
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
        lambda country_iso3, age_group="Y15-74", duration_group="TOTAL": {
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


def test_temporal_validation_gates_block_versioning():
    result = temporal_model_validation_status()

    assert result["ready_for_versioning"] is False
    assert result["blockers"] == ["external_calibration"]
    assert result["experimental"] == []
    assert result["missing"] == ["external_calibration"]
    assert set(result["scope_bounded"]) == {
        "skill_gap_duration",
        "local_employment_transition",
        "local_financial_transition",
    }

    assert result["gates"]["language_guided_hours"]["state"] == "supported"
    assert result["gates"]["remote_income_transition"]["state"] == "supported"
    assert result["model_scope"]["employment_mode"] == "preserved_remote_income_only"
    assert result["model_scope"]["essential_skill_gap"] == "none_allowed"


def test_local_employment_prefers_profile_age_group(monkeypatch):
    calls = []

    def fake_transition(country_iso3, age_group="Y15-74", duration_group="TOTAL"):
        calls.append(age_group)
        if age_group == "Y25-54":
            return {
                "country_iso3": country_iso3,
                "period": 2025,
                "age_group": "Y25-54",
                "duration_group": duration_group,
                "probability_pct": 30.0,
                "source_id": "EUROSTAT",
                "dataset_id": "lfsi_long_e01",
            }
        return None

    monkeypatch.setattr(module, "latest_labour_job_transition", fake_transition)

    profile = PersonalProfileResponse(
        profile_id="default",
        age=50,
        remote_work=False,
    )

    result = module.employment_temporal_evidence(
        profile,
        "IRL",
        {"status": "local_income_reference_available"},
        _career_ready(),
    )

    assert calls == ["Y25-54"]
    assert result["status"] == "available"
    assert result["source"]["age_group"] == "Y25-54"
    assert result["requested_age_group"] == "Y25-54"
    assert result["age_specific_baseline"] is True


def test_local_employment_falls_back_to_total_age_group(monkeypatch):
    calls = []

    def fake_transition(country_iso3, age_group="Y15-74", duration_group="TOTAL"):
        calls.append(age_group)
        if age_group == "Y15-74":
            return {
                "country_iso3": country_iso3,
                "period": 2025,
                "age_group": "Y15-74",
                "duration_group": duration_group,
                "probability_pct": 25.0,
                "source_id": "EUROSTAT",
                "dataset_id": "lfsi_long_e01",
            }
        return None

    monkeypatch.setattr(module, "latest_labour_job_transition", fake_transition)

    profile = PersonalProfileResponse(
        profile_id="default",
        age=50,
        remote_work=False,
    )

    result = module.employment_temporal_evidence(
        profile,
        "IRL",
        {"status": "local_income_reference_available"},
        _career_ready(),
    )

    assert calls == ["Y25-54", "Y15-74"]
    assert result["status"] == "available"
    assert result["source"]["age_group"] == "Y15-74"
    assert result["requested_age_group"] == "Y25-54"
    assert result["age_specific_baseline"] is False


def test_local_employment_rejects_age_outside_transition_population(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("transition datastore should not be queried")

    monkeypatch.setattr(module, "latest_labour_job_transition", fail_if_called)

    profile = PersonalProfileResponse(
        profile_id="default",
        age=80,
        remote_work=False,
    )

    result = module.employment_temporal_evidence(
        profile,
        "IRL",
        {"status": "local_income_reference_available"},
        _career_ready(),
    )

    assert result["status"] == "unavailable"
    assert result["reason"] == "profile_age_outside_eurostat_transition_population"
    assert result["profile_age"] == 80


def test_temporal_composition_uses_explicit_critical_path():
    stages = {
        "legal": {
            "status": "available",
            "weeks_min": 2,
            "weeks_max": 3,
        },
        "language": {
            "status": "available",
            "weeks_min": 10,
            "weeks_max": 20,
        },
        "skills": {
            "status": "available",
            "weeks_min": 4,
            "weeks_max": 8,
        },
        "employment": {
            "status": "available",
            "weeks_min": 13,
            "weeks_max": 26,
        },
        "financial": {
            "status": "available",
            "weeks_min": 2,
            "weeks_max": 4,
        },
    }

    result = compose_temporal_stages(stages)

    assert result == {
        "weeks_min": 25,
        "weeks_max": 50,
        "composition": "critical_path_v1",
        "stage_groups": {
            "preparation_parallel": ["legal", "language", "skills"],
            "employment_after_preparation": ["employment"],
            "financial_after_employment": ["financial"],
        },
    }


def test_temporal_composition_withholds_range_when_any_stage_unavailable():
    stages = {
        "legal": {"status": "available", "weeks_min": 0, "weeks_max": 0},
        "language": {"status": "available", "weeks_min": 4, "weeks_max": 8},
        "skills": {"status": "unavailable", "weeks_min": None, "weeks_max": None},
        "employment": {"status": "available", "weeks_min": 13, "weeks_max": 26},
        "financial": {"status": "available", "weeks_min": 0, "weeks_max": 0},
    }

    assert compose_temporal_stages(stages) is None


def test_temporal_graph_withholds_candidate_range_outside_v1_scope(monkeypatch):
    monkeypatch.setattr(
        module,
        "latest_labour_job_transition",
        lambda country_iso3, age_group="Y15-74", duration_group="TOTAL": {
            "country_iso3": country_iso3,
            "period": 2025,
            "age_group": age_group,
            "duration_group": duration_group,
            "probability_pct": 25.0,
            "source_id": "EUROSTAT",
            "dataset_id": "lfsi_long_e01",
        },
    )

    profile = PersonalProfileResponse(
        profile_id="default",
        remote_work=False,
        age=50,
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

    assert result["estimation_scope"]["in_scope"] is False
    assert "local_employment_mode_outside_v1_scope" in result["estimation_scope"]["blockers"]
    assert result["candidate_range"] is None
    assert result["calendar_ready"] is False


def test_temporal_graph_marks_remote_skill_ready_portable_income_case_in_scope():
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

    assert result["estimation_scope"]["in_scope"] is True
    assert result["estimation_scope"]["blockers"] == []
    assert result["calendar_ready"] is True
    assert result["candidate_range"] is not None



def test_temporal_validation_gate_reports_calibration_blockers(monkeypatch):
    monkeypatch.setattr(
        module,
        "calibration_status",
        lambda: {
            "externally_calibrated": False,
            "protocol_version": "ttv-calibration-protocol-v1",
            "holdout_seal": {"sealed": False, "holdout_sha256": None},
            "holdout_review": {"reviewed": False},
            "holdout_acceptance": {"status": "insufficient_sample"},
            "activation_readiness": {
                "ready_for_temporal_model_version": False,
                "blockers": [
                    "holdout_not_sealed",
                    "holdout_acceptance_not_passed",
                    "representativeness_review_missing",
                ],
            },
        },
    )

    result = module.temporal_model_validation_status()

    assert result["ready_for_versioning"] is False
    assert result["gates"]["external_calibration"]["state"] == "missing"
    assert result["gates"]["external_calibration"]["blockers"] == [
        "holdout_not_sealed",
        "holdout_acceptance_not_passed",
        "representativeness_review_missing",
    ]


def test_temporal_validation_gate_becomes_supported_after_external_calibration(
    monkeypatch,
):
    monkeypatch.setattr(
        module,
        "calibration_status",
        lambda: {
            "externally_calibrated": True,
            "protocol_version": "ttv-calibration-protocol-v1",
            "holdout_seal": {
                "sealed": True,
                "holdout_sha256": "abc123",
            },
            "holdout_review": {
                "reviewed": True,
                "representative": True,
                "cohort_coverage_adequate": True,
            },
            "holdout_acceptance": {
                "status": "passed",
                "passed": True,
            },
            "activation_readiness": {
                "ready_for_temporal_model_version": True,
                "blockers": [],
            },
        },
    )

    result = module.temporal_model_validation_status()

    assert result["ready_for_versioning"] is True
    assert result["blockers"] == []
    assert result["missing"] == []
    assert result["gates"]["external_calibration"] == {
        "state": "supported",
        "reason": (
            "sealed_holdout_passed_predeclared_criteria_and_"
            "representativeness_review"
        ),
        "protocol_version": "ttv-calibration-protocol-v1",
        "holdout_sha256": "abc123",
    }
