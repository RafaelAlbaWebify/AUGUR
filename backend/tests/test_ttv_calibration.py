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
    assert result["protocol_state"] == "definitions_frozen_acceptance_pending"
    assert result["protocol_version"] is None
    assert result["protocol_document"] == "docs/TTV_CALIBRATION_PROTOCOL.md"
    assert result["case_count"] == 0
    assert result["development_case_count"] == 0
    assert result["holdout_case_count"] == 0
    assert result["protocol_ready_for_holdout"] is False
    assert result["sample_roles"] == []
    assert result["externally_calibrated"] is False
    assert result["interval_coverage_pct"] is None
    assert result["stage_metrics"] == {}
    assert result["sample_role_metrics"] == {}


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
    assert result["mean_absolute_midpoint_error_weeks"] == 5.0
    assert result["mean_signed_midpoint_error_weeks"] == -5.0
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
        "mean_absolute_midpoint_error_weeks": 3.0,
        "mean_signed_midpoint_error_weeks": -3.0,
    }
    assert result["stage_metrics"]["employment"] == {
        "case_count": 1,
        "interval_coverage_pct": 0.0,
        "mean_absolute_midpoint_error_weeks": 9.0,
        "mean_signed_midpoint_error_weeks": -9.0,
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


def test_holdout_case_rejected_until_protocol_is_approved():
    case = {
        "case_id": "holdout-001",
        "country_iso3": "ESP",
        "employment_mode": "local",
        "engine_version": "ttv-temporal-evidence-v1",
        "composition": "critical_path_v1",
        "candidate_weeks_min": 8,
        "candidate_weeks_max": 18,
        "observed_weeks": 12,
        "sample_role": "holdout",
        "start_event_definition_version": "start-v1",
        "viability_outcome_definition_version": "outcome-v1",
    }

    with pytest.raises(
        ValueError,
        match="approved calibration protocol version",
    ):
        module.validate_calibration_case(case)


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
    assert status["sample_roles"] == ["development"]
    assert status["development_case_count"] == 1
    assert status["holdout_case_count"] == 0
    assert status["protocol_ready_for_holdout"] is False


def test_calibration_protocol_readiness_lists_unresolved_requirements():
    result = module.calibration_protocol_readiness()

    assert result["protocol_state"] == "definitions_frozen_acceptance_pending"
    assert result["ready_for_holdout_collection"] is False
    assert result["blockers"] == [
        "protocol_version",
        "acceptance_criteria",
    ]
    assert result["requirements"]["protocol_version"]["ready"] is False
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
    assert result["requirements"]["acceptance_criteria"]["ready"] is False


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
        "mean_absolute_midpoint_error_weeks": 0.0,
        "mean_signed_midpoint_error_weeks": 0.0,
    }
    assert result["sample_role_metrics"]["holdout"] == {
        "case_count": 0,
        "interval_coverage_pct": None,
        "mean_absolute_midpoint_error_weeks": None,
        "mean_signed_midpoint_error_weeks": None,
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
        "start_event_definition_version": "start-v1",
        "viability_outcome_definition_version": "outcome-v1",
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
    assert module.active_calibration_observation("IRL") is None

    status = module.calibration_status()
    assert status["development_case_count"] == 1
    assert status["holdout_case_count"] == 0
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
            observed_at=(started_at - timedelta(days=1)).isoformat(),
        )



def test_development_exchange_round_trip_excludes_personal_profile(
    monkeypatch,
    tmp_path,
):
    source_path = _use_temp_store(monkeypatch, tmp_path / "source")
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
