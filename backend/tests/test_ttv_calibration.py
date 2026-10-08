from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.db.bootstrap import initialize_sqlite
from app.services import ttv_calibration as module


def _use_temp_store(monkeypatch, tmp_path):
    path = tmp_path / "augur_test.sqlite"
    initialize_sqlite(path)
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(sqlite_path=path),
    )
    return path



def _candidate_ttv_result():
    return {
        "candidate_time_range": {
            "weeks_min": 10,
            "weeks_max": 25,
            "composition": "critical_path_v1",
        },
        "temporal_evidence": {
            "engine_version": "ttv-temporal-evidence-v1",
            "calendar_ready": True,
            "estimation_scope": {
                "scope_id": "ttv-estimation-scope-v1",
                "in_scope": True,
                "blockers": [],
            },
            "stages": {
                "language": {
                    "status": "available",
                    "current_cefr": "B1",
                    "target_cefr": "B2",
                    "guided_hours_min": 100,
                    "guided_hours_max": 250,
                    "weekly_study_hours": 10,
                    "weeks_min": 10,
                    "weeks_max": 25,
                }
            },
        },
    }

def test_empty_calibration_store_is_ready_but_not_calibrated(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    result = module.calibration_status()

    assert result["infrastructure_ready"] is True
    assert result["protocol_state"] == "protocol_v1_frozen_holdout_collection_enabled"
    assert result["protocol_version"] == "ttv-calibration-protocol-v1"
    assert result["protocol_document"] == "docs/TTV_CALIBRATION_PROTOCOL.md"
    assert result["case_count"] == 0
    assert result["development_case_count"] == 0
    assert result["holdout_case_count"] == 0
    assert result["protocol_ready_for_holdout"] is True
    assert result["sample_roles"] == []
    assert result["externally_calibrated"] is False
    assert result["interval_coverage_pct"] is None
    assert result["stage_metrics"] == {}
    assert result["sample_role_metrics"] == {}
    assert result["context_summary"] == {
        "context_case_count": 0,
        "current_cefr_levels": [],
        "target_cefr_levels": [],
        "achieved_cefr_levels": [],
        "outcome_evidence_types": [],
        "weekly_study_hours": [],
    }


def test_calibration_metrics_are_descriptive_only(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    module.upsert_calibration_case(
        {
            "case_id": "case-001",
            "country_iso3": "IRL",
            "employment_mode": "local",
            "engine_version": "ttv-temporal-evidence-v1",
            "composition": "critical_path_v1",
            "candidate_weeks_min": 10,
            "candidate_weeks_max": 20,
            "observed_weeks": 15,
            "source_label": "anonymous retrospective case",
        }
    )
    module.upsert_calibration_case(
        {
            "case_id": "case-002",
            "country_iso3": "PRT",
            "employment_mode": "remote",
            "engine_version": "ttv-temporal-evidence-v1",
            "composition": "critical_path_v1",
            "candidate_weeks_min": 10,
            "candidate_weeks_max": 20,
            "observed_weeks": 25,
        }
    )

    result = module.calibration_status()

    assert result["case_count"] == 2
    assert result["country_count"] == 2
    assert result["employment_modes"] == ["local", "remote"]
    assert result["interval_coverage_pct"] == 50.0
    assert result["mean_interval_width_weeks"] == 10.0
    assert result["median_interval_width_weeks"] == 10.0
    assert result["mean_absolute_midpoint_error_weeks"] == 5.0
    assert result["mean_signed_midpoint_error_weeks"] == -5.0
    assert result["outside_interval_count"] == 1
    assert result["below_interval_count"] == 0
    assert result["above_interval_count"] == 1
    assert result["mean_miss_distance_weeks"] == 5.0
    assert result["sample_role_metrics"]["development"]["case_count"] == 2
    assert result["sample_role_metrics"]["development"]["interval_coverage_pct"] == 50.0
    assert result["sample_role_metrics"]["holdout"]["case_count"] == 0
    assert result["sample_role_metrics"]["holdout"]["interval_coverage_pct"] is None
    assert result["externally_calibrated"] is False


def test_calibration_csv_import_validates_and_upserts(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    csv_path = tmp_path / "calibration.csv"
    csv_path.write_text(
        "case_id,country_iso3,employment_mode,engine_version,"
        "composition,candidate_weeks_min,candidate_weeks_max,"
        "observed_weeks,source_label,observed_at\n"
        "case-001,ESP,local,ttv-temporal-evidence-v1,"
        "critical_path_v1,8,18,12,anonymous pilot,2026-09-01\n",
        encoding="utf-8",
    )

    imported = module.import_calibration_csv(csv_path)
    status = module.calibration_status()

    assert imported["imported_count"] == 1
    assert imported["case_ids"] == ["case-001"]
    assert status["case_count"] == 1
    assert status["interval_coverage_pct"] == 100.0
    assert status["externally_calibrated"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("composition", "parallel_max"),
        ("employment_mode", "unknown"),
        ("candidate_weeks_min", -1),
        ("observed_weeks", -1),
    ],
)
def test_calibration_case_rejects_invalid_values(field, value):
    case = {
        "case_id": "case-001",
        "country_iso3": "ESP",
        "employment_mode": "local",
        "engine_version": "ttv-temporal-evidence-v1",
        "composition": "critical_path_v1",
        "candidate_weeks_min": 8,
        "candidate_weeks_max": 18,
        "observed_weeks": 12,
    }
    case[field] = value

    with pytest.raises(ValueError):
        module.validate_calibration_case(case)


def test_stage_level_calibration_metrics_are_reported(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    module.upsert_calibration_case(
        {
            "case_id": "case-stage-001",
            "country_iso3": "IRL",
            "employment_mode": "local",
            "engine_version": "ttv-temporal-evidence-v1",
            "composition": "critical_path_v1",
            "candidate_weeks_min": 20,
            "candidate_weeks_max": 40,
            "observed_weeks": 30,
            "stage_timings": {
                "language": {
                    "candidate_weeks_min": 10,
                    "candidate_weeks_max": 20,
                    "observed_weeks": 18,
                },
                "employment": {
                    "candidate_weeks_min": 10,
                    "candidate_weeks_max": 20,
                    "observed_weeks": 24,
                },
            },
        }
    )

    result = module.calibration_status()

    assert result["stage_metrics"]["language"] == {
        "case_count": 1,
        "interval_coverage_pct": 100.0,
        "mean_interval_width_weeks": 10.0,
        "median_interval_width_weeks": 10.0,
        "mean_absolute_midpoint_error_weeks": 3.0,
        "mean_signed_midpoint_error_weeks": -3.0,
        "outside_interval_count": 0,
        "below_interval_count": 0,
        "above_interval_count": 0,
        "mean_miss_distance_weeks": 0.0,
    }
    assert result["stage_metrics"]["employment"] == {
        "case_count": 1,
        "interval_coverage_pct": 0.0,
        "mean_interval_width_weeks": 10.0,
        "median_interval_width_weeks": 10.0,
        "mean_absolute_midpoint_error_weeks": 9.0,
        "mean_signed_midpoint_error_weeks": -9.0,
        "outside_interval_count": 1,
        "below_interval_count": 0,
        "above_interval_count": 1,
        "mean_miss_distance_weeks": 4.0,
    }


def test_stage_level_calibration_rejects_partial_timing_payload():
    case = {
        "case_id": "case-stage-001",
        "country_iso3": "ESP",
        "employment_mode": "local",
        "engine_version": "ttv-temporal-evidence-v1",
        "composition": "critical_path_v1",
        "candidate_weeks_min": 8,
        "candidate_weeks_max": 18,
        "observed_weeks": 12,
        "stage_timings": {
            "language": {
                "candidate_weeks_min": 4,
                "candidate_weeks_max": 8,
            }
        },
    }

    with pytest.raises(ValueError, match="requires candidate min/max and observed weeks"):
        module.validate_calibration_case(case)


def test_holdout_case_requires_frozen_protocol_and_definitions():
    base = {
        "case_id": "holdout-001",
        "country_iso3": "IRL",
        "employment_mode": "remote",
        "engine_version": "ttv-temporal-evidence-v1",
        "composition": "critical_path_v1",
        "candidate_weeks_min": 8,
        "candidate_weeks_max": 18,
        "observed_weeks": 12,
        "sample_role": "holdout",
        "start_event_definition_version": module.CALIBRATION_START_EVENT_DEFINITION_VERSION,
        "viability_outcome_definition_version": module.CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION,
    }

    with pytest.raises(
        ValueError,
        match="calibration_protocol_version",
    ):
        module.validate_calibration_case(base)

    with pytest.raises(
        ValueError,
        match="frozen start-event definition version",
    ):
        module.validate_calibration_case({
            **base,
            "calibration_protocol_version": module.CALIBRATION_PROTOCOL_VERSION,
            "start_event_definition_version": "wrong-start",
        })

    validated = module.validate_calibration_case({
        **base,
        "calibration_protocol_version": module.CALIBRATION_PROTOCOL_VERSION,
    })

    assert validated["sample_role"] == "holdout"
    assert validated["calibration_protocol_version"] == "ttv-calibration-protocol-v1"


def test_development_case_defaults_to_exploratory_sample_role(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    saved = module.upsert_calibration_case(
        {
            "case_id": "dev-001",
            "country_iso3": "IRL",
            "employment_mode": "remote",
            "engine_version": "ttv-temporal-evidence-v1",
            "composition": "critical_path_v1",
            "candidate_weeks_min": 4,
            "candidate_weeks_max": 8,
            "observed_weeks": 6,
        }
    )

    status = module.calibration_status()

    assert saved["sample_role"] == "development"
    assert saved["start_event_definition_version"] is None
    assert saved["viability_outcome_definition_version"] is None
    assert saved["calibration_protocol_version"] is None
    assert status["sample_roles"] == ["development"]
    assert status["development_case_count"] == 1
    assert status["holdout_case_count"] == 0
    assert status["protocol_ready_for_holdout"] is False


def test_calibration_protocol_readiness_lists_unresolved_requirements():
    result = module.calibration_protocol_readiness()

    assert result["protocol_state"] == "protocol_v1_frozen_holdout_collection_enabled"
    assert result["ready_for_holdout_collection"] is True
    assert result["blockers"] == []
    assert result["requirements"]["protocol_version"] == {
        "ready": True,
        "version": "ttv-calibration-protocol-v1",
    }
    assert result["requirements"]["start_event_definition"] == {
        "ready": True,
        "version": "ttv-start-active-language-transition-v1",
    }
    assert result["requirements"]["viability_outcome_definition"] == {
        "ready": True,
        "version": "ttv-outcome-b2-remote-viability-v1",
    }
    assert result["requirements"]["inclusion_exclusion_rules"] == {
        "ready": True,
        "version": "ttv-inclusion-remote-scope-v1",
    }
    assert result["requirements"]["acceptance_criteria"] == {
        "ready": True,
        "version": "ttv-acceptance-criteria-v1",
    }
    assert result["acceptance_criteria"]["minimum_holdout_cases"] == 60
    assert result["acceptance_criteria"]["minimum_interval_coverage_pct"] == 80.0


def test_sample_role_metrics_keep_development_and_holdout_separate(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    module.upsert_calibration_case(
        {
            "case_id": "dev-role-001",
            "country_iso3": "ESP",
            "employment_mode": "remote",
            "engine_version": "ttv-temporal-evidence-v1",
            "composition": "critical_path_v1",
            "candidate_weeks_min": 4,
            "candidate_weeks_max": 8,
            "observed_weeks": 6,
            "sample_role": "development",
        }
    )

    result = module.calibration_status()

    assert result["development_case_count"] == 1
    assert result["holdout_case_count"] == 0
    assert result["sample_role_metrics"]["development"] == {
        "case_count": 1,
        "interval_coverage_pct": 100.0,
        "mean_interval_width_weeks": 4.0,
        "median_interval_width_weeks": 4.0,
        "mean_absolute_midpoint_error_weeks": 0.0,
        "mean_signed_midpoint_error_weeks": 0.0,
        "outside_interval_count": 0,
        "below_interval_count": 0,
        "above_interval_count": 0,
        "mean_miss_distance_weeks": 0.0,
    }
    assert result["sample_role_metrics"]["holdout"] == {
        "case_count": 0,
        "interval_coverage_pct": None,
        "mean_interval_width_weeks": None,
        "median_interval_width_weeks": None,
        "mean_absolute_midpoint_error_weeks": None,
        "mean_signed_midpoint_error_weeks": None,
        "outside_interval_count": 0,
        "below_interval_count": 0,
        "above_interval_count": 0,
        "mean_miss_distance_weeks": None,
    }


def test_calibration_preflight_separates_v1_eligible_cases():
    result = module.calibration_batch_preflight([
        {
            "case_id": "remote-v1",
            "country_iso3": "IRL",
            "employment_mode": "remote",
            "engine_version": "ttv-temporal-evidence-v1",
            "composition": "critical_path_v1",
        },
        {
            "case_id": "local-dev",
            "country_iso3": "ESP",
            "employment_mode": "local",
            "engine_version": "ttv-temporal-evidence-v1",
            "composition": "critical_path_v1",
        },
    ])

    assert result["case_count"] == 2
    assert result["eligible_case_count"] == 1
    assert result["ineligible_case_count"] == 1
    assert result["all_cases_eligible"] is False
    assert result["cases"][0]["eligible_for_v1_holdout"] is True
    assert result["cases"][1]["blockers"] == [
        "employment_mode_outside_ttv_v1_scope"
    ]


def test_calibration_protocol_readiness_exposes_holdout_scope():
    result = module.calibration_protocol_readiness()

    assert result["holdout_scope"]["scope_id"] == "ttv-estimation-scope-v1"
    assert result["holdout_scope"]["employment_modes"] == ["remote"]
    assert result["holdout_scope"]["engine_versions"] == [
        "ttv-temporal-evidence-v1"
    ]
    assert result["holdout_scope"]["composition_versions"] == [
        "critical_path_v1"
    ]


def test_holdout_scope_rejects_local_case_after_protocol_gate(monkeypatch):
    monkeypatch.setattr(
        module,
        "CALIBRATION_PROTOCOL_VERSION",
        "ttv-calibration-protocol-v1",
    )

    case = {
        "case_id": "holdout-local-001",
        "country_iso3": "ESP",
        "employment_mode": "local",
        "engine_version": "ttv-temporal-evidence-v1",
        "composition": "critical_path_v1",
        "candidate_weeks_min": 8,
        "candidate_weeks_max": 18,
        "observed_weeks": 12,
        "sample_role": "holdout",
        "start_event_definition_version": module.CALIBRATION_START_EVENT_DEFINITION_VERSION,
        "viability_outcome_definition_version": module.CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION,
        "calibration_protocol_version": module.CALIBRATION_PROTOCOL_VERSION,
    }

    with pytest.raises(
        ValueError,
        match="outside TTV v1 calibration scope",
    ):
        module.validate_calibration_case(case)



def test_opt_in_observation_lifecycle_creates_development_case(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    started = module.start_calibration_observation(
        "IRL",
        _candidate_ttv_result(),
    )
    duplicate = module.start_calibration_observation(
        "IRL",
        _candidate_ttv_result(),
    )

    assert started["status"] == "active"
    assert duplicate["case_id"] == started["case_id"]
    assert started["baseline"]["language"]["current_cefr"] == "B1"
    assert started["baseline"]["language"]["target_cefr"] == "B2"

    started_at = datetime.fromisoformat(started["started_at"])
    observed_at = started_at + timedelta(days=84)

    completed = module.complete_calibration_observation(
        started["case_id"],
        achieved_cefr="B2",
        evidence_type="official_exam",
        observed_at=observed_at.isoformat(),
    )

    assert completed["observation"]["status"] == "completed"
    assert completed["calibration_case"]["sample_role"] == "development"
    assert completed["calibration_case"]["employment_mode"] == "remote"
    assert completed["calibration_case"]["observed_weeks"] == 12.0
    assert completed["calibration_case"]["stage_timings"]["language"] == {
        "candidate_weeks_min": 10.0,
        "candidate_weeks_max": 25.0,
        "observed_weeks": 12.0,
    }
    assert completed["calibration_case"]["context"] == {
        "scope_id": "ttv-estimation-scope-v1",
        "current_cefr": "B1",
        "target_cefr": "B2",
        "weekly_study_hours": 10.0,
        "guided_hours_min": 100.0,
        "guided_hours_max": 250.0,
        "achieved_cefr": "B2",
        "outcome_evidence_type": "official_exam",
    }
    assert module.active_calibration_observation("IRL") is None

    status = module.calibration_status()
    assert status["development_case_count"] == 1
    assert status["holdout_case_count"] == 0
    assert status["context_summary"] == {
        "context_case_count": 1,
        "current_cefr_levels": ["B1"],
        "target_cefr_levels": ["B2"],
        "achieved_cefr_levels": ["B2"],
        "outcome_evidence_types": ["official_exam"],
        "weekly_study_hours": [10.0],
    }
    assert status["externally_calibrated"] is False


def test_opt_in_observation_rejects_out_of_scope_candidate(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)
    result = _candidate_ttv_result()
    result["temporal_evidence"]["estimation_scope"]["in_scope"] = False
    result["temporal_evidence"]["estimation_scope"]["blockers"] = [
        "local_employment_mode_outside_v1_scope"
    ]
    result["candidate_time_range"] = None

    with pytest.raises(ValueError, match="in-scope v1 case"):
        module.start_calibration_observation("ESP", result)


def test_cancelled_observation_does_not_create_calibration_case(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    started = module.start_calibration_observation(
        "PRT",
        _candidate_ttv_result(),
    )
    cancelled = module.cancel_calibration_observation(started["case_id"])

    assert cancelled["status"] == "cancelled"
    assert module.active_calibration_observation("PRT") is None
    assert module.calibration_status()["case_count"] == 0


def test_observation_completion_rejects_date_before_start(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    started = module.start_calibration_observation(
        "IRL",
        _candidate_ttv_result(),
    )
    started_at = datetime.fromisoformat(started["started_at"])

    with pytest.raises(ValueError, match="must not be before"):
        module.complete_calibration_observation(
            started["case_id"],
            achieved_cefr="B2",
            evidence_type="cefr_aligned_assessment",
            observed_at=(started_at - timedelta(days=1)).isoformat(),
        )



def test_development_exchange_round_trip_excludes_personal_profile(
    monkeypatch,
    tmp_path,
):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _use_temp_store(monkeypatch, source_dir)
    module.upsert_calibration_case(
        {
            "case_id": "exchange-001",
            "country_iso3": "IRL",
            "employment_mode": "remote",
            "engine_version": "ttv-temporal-evidence-v1",
            "composition": "critical_path_v1",
            "candidate_weeks_min": 10,
            "candidate_weeks_max": 25,
            "observed_weeks": 12,
            "sample_role": "development",
            "start_event_definition_version": "ttv-start-active-language-transition-v1",
            "viability_outcome_definition_version": "ttv-outcome-b2-remote-viability-v1",
            "source_label": "local provenance that must not travel",
            "observed_at": "2027-01-01T00:00:00+00:00",
            "stage_timings": {
                "language": {
                    "candidate_weeks_min": 10,
                    "candidate_weeks_max": 25,
                    "observed_weeks": 12,
                }
            },
            "context": {
                "scope_id": "ttv-estimation-scope-v1",
                "current_cefr": "B1",
                "target_cefr": "B2",
                "weekly_study_hours": 10,
                "guided_hours_min": 100,
                "guided_hours_max": 250,
                "achieved_cefr": "B2",
                "outcome_evidence_type": "official_exam",
            },
        }
    )

    package = module.export_development_calibration_package()

    assert package["exchange_version"] == "ttv-development-exchange-v1"
    assert package["case_count"] == 1
    assert package["privacy"]["contains_full_profile"] is False
    exported = package["cases"][0]
    assert exported["case_id"] == "exchange-001"
    assert "source_label" not in exported
    assert "observed_at" not in exported
    assert "imported_at" not in exported
    assert "profile" not in exported
    assert exported["context"] == {
        "scope_id": "ttv-estimation-scope-v1",
        "current_cefr": "B1",
        "target_cefr": "B2",
        "weekly_study_hours": 10.0,
        "guided_hours_min": 100.0,
        "guided_hours_max": 250.0,
        "achieved_cefr": "B2",
        "outcome_evidence_type": "official_exam",
    }

    target_dir = tmp_path / "target"
    target_dir.mkdir()
    target_path = target_dir / "augur_test.sqlite"
    initialize_sqlite(target_path)
    monkeypatch.setattr(
        module,
        "settings",
        SimpleNamespace(sqlite_path=target_path),
    )

    imported = module.import_development_calibration_package(package)

    assert imported["imported_count"] == 1
    assert imported["case_ids"] == ["exchange-001"]
    assert imported["calibration_status"]["development_case_count"] == 1
    assert imported["calibration_status"]["holdout_case_count"] == 0
    assert imported["calibration_status"]["context_summary"] == {
        "context_case_count": 1,
        "current_cefr_levels": ["B1"],
        "target_cefr_levels": ["B2"],
        "achieved_cefr_levels": ["B2"],
        "outcome_evidence_types": ["official_exam"],
        "weekly_study_hours": [10.0],
    }
    assert imported["calibration_status"]["externally_calibrated"] is False


def test_development_exchange_rejects_holdout_role(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)
    package = {
        "exchange_version": "ttv-development-exchange-v1",
        "cases": [
            {
                "case_id": "holdout-in-disguise",
                "country_iso3": "IRL",
                "employment_mode": "remote",
                "engine_version": "ttv-temporal-evidence-v1",
                "composition": "critical_path_v1",
                "candidate_weeks_min": 10,
                "candidate_weeks_max": 25,
                "observed_weeks": 12,
                "sample_role": "holdout",
                "stage_timings": {},
            }
        ],
    }

    with pytest.raises(ValueError, match="development cases only"):
        module.import_development_calibration_package(package)


def test_development_exchange_rejects_unknown_version(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    with pytest.raises(ValueError, match="unsupported"):
        module.import_development_calibration_package(
            {
                "exchange_version": "unknown-v9",
                "cases": [],
            }
        )



@pytest.mark.parametrize(
    "context",
    [
        {"current_cefr": "Z9"},
        {"target_cefr": "B9"},
        {"weekly_study_hours": 0},
        {"weekly_study_hours": 81},
        {"guided_hours_min": 100},
        {"guided_hours_min": 250, "guided_hours_max": 100},
    ],
)
def test_calibration_context_validates_cefr_and_study_intensity(context):
    case = {
        "case_id": "context-invalid",
        "country_iso3": "IRL",
        "employment_mode": "remote",
        "engine_version": "ttv-temporal-evidence-v1",
        "composition": "critical_path_v1",
        "candidate_weeks_min": 10,
        "candidate_weeks_max": 25,
        "observed_weeks": 12,
        "context": context,
    }

    with pytest.raises(ValueError):
        module.validate_calibration_case(case)


def test_calibration_context_normalizes_valid_cohort_fields():
    result = module.validate_calibration_case(
        {
            "case_id": "context-valid",
            "country_iso3": "IRL",
            "employment_mode": "remote",
            "engine_version": "ttv-temporal-evidence-v1",
            "composition": "critical_path_v1",
            "candidate_weeks_min": 10,
            "candidate_weeks_max": 25,
            "observed_weeks": 12,
            "context": {
                "scope_id": "ttv-estimation-scope-v1",
                "current_cefr": "b1",
                "target_cefr": "b2",
                "weekly_study_hours": 10,
                "guided_hours_min": 100,
                "guided_hours_max": 250,
            },
        }
    )

    assert result["context"] == {
        "scope_id": "ttv-estimation-scope-v1",
        "current_cefr": "B1",
        "target_cefr": "B2",
        "weekly_study_hours": 10.0,
        "guided_hours_min": 100.0,
        "guided_hours_max": 250.0,
    }



@pytest.mark.parametrize(
    "achieved_cefr,evidence_type,match",
    [
        ("B1", "official_exam", "achieved_cefr"),
        ("", "official_exam", "achieved_cefr"),
        ("B2", "", "evidence_type"),
        ("B2", "self_report", "evidence_type"),
    ],
)
def test_observation_completion_requires_documented_cefr_evidence(
    monkeypatch,
    tmp_path,
    achieved_cefr,
    evidence_type,
    match,
):
    _use_temp_store(monkeypatch, tmp_path)
    started = module.start_calibration_observation(
        "IRL",
        _candidate_ttv_result(),
    )

    with pytest.raises(ValueError, match=match):
        module.complete_calibration_observation(
            started["case_id"],
            achieved_cefr=achieved_cefr,
            evidence_type=evidence_type,
        )



def test_calibration_context_rejects_sub_b2_achieved_outcome():
    case = {
        "case_id": "context-sub-b2",
        "country_iso3": "IRL",
        "employment_mode": "remote",
        "engine_version": "ttv-temporal-evidence-v1",
        "composition": "critical_path_v1",
        "candidate_weeks_min": 10,
        "candidate_weeks_max": 25,
        "observed_weeks": 12,
        "context": {
            "scope_id": "ttv-estimation-scope-v1",
            "current_cefr": "A2",
            "target_cefr": "B2",
            "achieved_cefr": "B1",
            "outcome_evidence_type": "official_exam",
            "weekly_study_hours": 10,
            "guided_hours_min": 100,
            "guided_hours_max": 250,
        },
    }

    with pytest.raises(ValueError, match="achieved_cefr"):
        module.validate_calibration_case(case)


def _holdout_case(index, lower=10.0, upper=20.0, observed=15.0):
    return {
        "case_id": f"holdout-{index:03d}",
        "country_iso3": "IRL",
        "employment_mode": "remote",
        "engine_version": "ttv-temporal-evidence-v1",
        "composition": "critical_path_v1",
        "sample_role": "holdout",
        "candidate_weeks_min": lower,
        "candidate_weeks_max": upper,
        "observed_weeks": observed,
    }


def test_holdout_acceptance_reports_insufficient_sample():
    result = module.evaluate_holdout_acceptance([
        _holdout_case(index)
        for index in range(20)
    ])

    assert result["status"] == "insufficient_sample"
    assert result["passed"] is False
    assert result["eligible_holdout_case_count"] == 20
    assert result["checks"]["minimum_holdout_cases"]["passed"] is False
    assert result["representativeness_review_required"] is True


def test_holdout_acceptance_can_pass_frozen_numeric_thresholds():
    cases = [
        _holdout_case(
            index,
            lower=10.0,
            upper=20.0,
            observed=15.0 if index % 5 else 18.0,
        )
        for index in range(60)
    ]

    result = module.evaluate_holdout_acceptance(cases)

    assert result["status"] == "passed"
    assert result["passed"] is True
    assert result["metrics"]["interval_coverage_pct"] == 100.0
    assert all(item["passed"] for item in result["checks"].values())


def test_holdout_acceptance_fails_poor_coverage_and_bias():
    cases = [
        _holdout_case(
            index,
            lower=10.0,
            upper=20.0,
            observed=32.0,
        )
        for index in range(60)
    ]

    result = module.evaluate_holdout_acceptance(cases)

    assert result["status"] == "failed"
    assert result["passed"] is False
    assert result["checks"]["interval_coverage_pct"]["passed"] is False
    assert result["checks"]["absolute_mean_signed_midpoint_error_weeks"]["passed"] is False
    assert result["checks"]["above_interval_rate_pct"]["passed"] is False



def _valid_holdout_case(case_id="holdout-immutable-001"):
    return {
        "case_id": case_id,
        "country_iso3": "IRL",
        "employment_mode": "remote",
        "engine_version": "ttv-temporal-evidence-v1",
        "composition": "critical_path_v1",
        "candidate_weeks_min": 10,
        "candidate_weeks_max": 25,
        "observed_weeks": 16,
        "sample_role": "holdout",
        "start_event_definition_version": module.CALIBRATION_START_EVENT_DEFINITION_VERSION,
        "viability_outcome_definition_version": module.CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION,
        "calibration_protocol_version": module.CALIBRATION_PROTOCOL_VERSION,
    }


def test_holdout_case_is_immutable_after_import(monkeypatch, tmp_path):
    _use_temp_store(monkeypatch, tmp_path)

    saved = module.upsert_calibration_case(_valid_holdout_case())
    assert saved["sample_role"] == "holdout"

    with pytest.raises(ValueError, match="immutable once imported"):
        module.upsert_calibration_case({
            **_valid_holdout_case(),
            "observed_weeks": 17,
        })

    status = module.calibration_status()
    assert status["holdout_case_count"] == 1
    assert status["calibration_protocol_versions"] == [
        "ttv-calibration-protocol-v1"
    ]


def test_csv_import_validates_entire_batch_before_writing(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    csv_path = tmp_path / "batch.csv"
    csv_path.write_text(
        "case_id,country_iso3,employment_mode,engine_version,"
        "composition,candidate_weeks_min,candidate_weeks_max,"
        "observed_weeks,sample_role\n"
        "valid-001,IRL,remote,ttv-temporal-evidence-v1,"
        "critical_path_v1,10,25,16,development\n"
        "invalid-002,IRL,remote,ttv-temporal-evidence-v1,"
        "critical_path_v1,25,10,16,development\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid calibration row 3"):
        module.import_calibration_csv(csv_path)

    assert module.calibration_status()["case_count"] == 0


def test_csv_import_rejects_duplicate_case_ids_before_writing(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    csv_path = tmp_path / "duplicate.csv"
    csv_path.write_text(
        "case_id,country_iso3,employment_mode,engine_version,"
        "composition,candidate_weeks_min,candidate_weeks_max,"
        "observed_weeks,sample_role\n"
        "dup-001,IRL,remote,ttv-temporal-evidence-v1,"
        "critical_path_v1,10,25,16,development\n"
        "dup-001,IRL,remote,ttv-temporal-evidence-v1,"
        "critical_path_v1,10,25,17,development\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate case_id"):
        module.import_calibration_csv(csv_path)

    assert module.calibration_status()["case_count"] == 0



def test_holdout_csv_import_requires_protocol_bound_holdout_rows(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    csv_path = tmp_path / "holdout.csv"
    csv_path.write_text(
        "case_id,country_iso3,employment_mode,engine_version,composition,"
        "candidate_weeks_min,candidate_weeks_max,observed_weeks,"
        "sample_role,start_event_definition_version,"
        "viability_outcome_definition_version,calibration_protocol_version\n"
        "holdout-001,IRL,remote,ttv-temporal-evidence-v1,critical_path_v1,"
        "10,25,16,holdout,"
        "ttv-start-active-language-transition-v1,"
        "ttv-outcome-b2-remote-viability-v1,"
        "ttv-calibration-protocol-v1\n",
        encoding="utf-8",
    )

    result = module.import_holdout_calibration_csv(csv_path)

    assert result["import_mode"] == "holdout"
    assert result["frozen_protocol_version"] == "ttv-calibration-protocol-v1"
    assert result["acceptance_criteria_version"] == "ttv-acceptance-criteria-v1"
    assert result["imported_count"] == 1

    status = module.calibration_status()
    assert status["holdout_case_count"] == 1
    assert status["calibration_protocol_versions"] == [
        "ttv-calibration-protocol-v1"
    ]


def test_holdout_csv_import_rejects_mixed_development_rows_before_write(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    csv_path = tmp_path / "mixed.csv"
    csv_path.write_text(
        "case_id,country_iso3,employment_mode,engine_version,composition,"
        "candidate_weeks_min,candidate_weeks_max,observed_weeks,"
        "sample_role,start_event_definition_version,"
        "viability_outcome_definition_version,calibration_protocol_version\n"
        "holdout-001,IRL,remote,ttv-temporal-evidence-v1,critical_path_v1,"
        "10,25,16,holdout,"
        "ttv-start-active-language-transition-v1,"
        "ttv-outcome-b2-remote-viability-v1,"
        "ttv-calibration-protocol-v1\n"
        "dev-001,IRL,remote,ttv-temporal-evidence-v1,critical_path_v1,"
        "10,25,15,development,"
        "ttv-start-active-language-transition-v1,"
        "ttv-outcome-b2-remote-viability-v1,"
        "ttv-calibration-protocol-v1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="sample_role must be holdout"):
        module.import_holdout_calibration_csv(csv_path)

    assert module.calibration_status()["case_count"] == 0


def test_holdout_csv_import_rejects_wrong_protocol_before_write(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    csv_path = tmp_path / "wrong-protocol.csv"
    csv_path.write_text(
        "case_id,country_iso3,employment_mode,engine_version,composition,"
        "candidate_weeks_min,candidate_weeks_max,observed_weeks,"
        "sample_role,start_event_definition_version,"
        "viability_outcome_definition_version,calibration_protocol_version\n"
        "holdout-001,IRL,remote,ttv-temporal-evidence-v1,critical_path_v1,"
        "10,25,16,holdout,"
        "ttv-start-active-language-transition-v1,"
        "ttv-outcome-b2-remote-viability-v1,"
        "ttv-calibration-protocol-v0\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="calibration_protocol_version"):
        module.import_holdout_calibration_csv(csv_path)

    assert module.calibration_status()["case_count"] == 0
