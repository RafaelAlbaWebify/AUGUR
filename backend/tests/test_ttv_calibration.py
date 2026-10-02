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
    assert result["case_count"] == 0
    assert result["externally_calibrated"] is False
    assert result["interval_coverage_pct"] is None


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
