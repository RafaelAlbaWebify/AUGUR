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


def test_empty_calibration_store_is_ready_but_not_calibrated(
    monkeypatch,
    tmp_path,
):
    _use_temp_store(monkeypatch, tmp_path)

    result = module.calibration_status()

    assert result["infrastructure_ready"] is True
    assert result["protocol_state"] == "draft_not_approved"
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

    assert result["protocol_state"] == "draft_not_approved"
    assert result["ready_for_holdout_collection"] is False
    assert result["blockers"] == [
        "protocol_version",
        "start_event_definition",
        "viability_outcome_definition",
        "inclusion_exclusion_rules",
        "acceptance_criteria",
    ]
    assert result["requirements"]["protocol_version"]["ready"] is False
    assert result["requirements"]["start_event_definition"]["version"] is None


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
