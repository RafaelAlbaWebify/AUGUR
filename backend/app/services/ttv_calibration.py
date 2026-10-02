from __future__ import annotations

import csv
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


CALIBRATION_SCHEMA_VERSION = "ttv-calibration-v1"
SUPPORTED_EMPLOYMENT_MODES = {"remote", "local"}
SUPPORTED_COMPOSITIONS = {"critical_path_v1"}


def _as_float(value, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc

    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")

    return result


def validate_calibration_case(case: dict) -> dict:
    case_id = str(case.get("case_id") or "").strip()
    country_iso3 = str(case.get("country_iso3") or "").strip().upper()
    employment_mode = str(case.get("employment_mode") or "").strip().lower()
    engine_version = str(case.get("engine_version") or "").strip()
    composition = str(case.get("composition") or "").strip()

    if not case_id:
        raise ValueError("case_id is required")
    if len(country_iso3) != 3 or not country_iso3.isalpha():
        raise ValueError("country_iso3 must be an ISO3-style code")
    if employment_mode not in SUPPORTED_EMPLOYMENT_MODES:
        raise ValueError(
            "employment_mode must be one of: "
            + ", ".join(sorted(SUPPORTED_EMPLOYMENT_MODES))
        )
    if not engine_version:
        raise ValueError("engine_version is required")
    if composition not in SUPPORTED_COMPOSITIONS:
        raise ValueError(
            "composition must be one of: "
            + ", ".join(sorted(SUPPORTED_COMPOSITIONS))
        )

    candidate_min = _as_float(
        case.get("candidate_weeks_min"),
        "candidate_weeks_min",
    )
    candidate_max = _as_float(
        case.get("candidate_weeks_max"),
        "candidate_weeks_max",
    )
    observed = _as_float(
        case.get("observed_weeks"),
        "observed_weeks",
    )

    if candidate_min < 0:
        raise ValueError("candidate_weeks_min must be >= 0")
    if candidate_max < candidate_min:
        raise ValueError(
            "candidate_weeks_max must be >= candidate_weeks_min"
        )
    if observed < 0:
        raise ValueError("observed_weeks must be >= 0")

    source_label = str(case.get("source_label") or "").strip() or None
    observed_at = str(case.get("observed_at") or "").strip() or None

    return {
        "case_id": case_id,
        "country_iso3": country_iso3,
        "employment_mode": employment_mode,
        "engine_version": engine_version,
        "composition": composition,
        "candidate_weeks_min": candidate_min,
        "candidate_weeks_max": candidate_max,
        "observed_weeks": observed,
        "source_label": source_label,
        "observed_at": observed_at,
    }


def upsert_calibration_case(case: dict) -> dict:
    normalized = validate_calibration_case(case)
    imported_at = datetime.now(timezone.utc).isoformat()

    con = sqlite3.connect(settings.sqlite_path)
    try:
        con.execute(
            """
            INSERT OR REPLACE INTO ttv_calibration_cases (
                case_id,
                country_iso3,
                employment_mode,
                engine_version,
                composition,
                candidate_weeks_min,
                candidate_weeks_max,
                observed_weeks,
                source_label,
                observed_at,
                imported_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized["case_id"],
                normalized["country_iso3"],
                normalized["employment_mode"],
                normalized["engine_version"],
                normalized["composition"],
                normalized["candidate_weeks_min"],
                normalized["candidate_weeks_max"],
                normalized["observed_weeks"],
                normalized["source_label"],
                normalized["observed_at"],
                imported_at,
            ),
        )
        con.commit()
    finally:
        con.close()

    return {
        **normalized,
        "imported_at": imported_at,
    }


def import_calibration_csv(path: str | Path) -> dict:
    source_path = Path(path).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    imported = 0
    case_ids: list[str] = []

    with source_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)
        required = {
            "case_id",
            "country_iso3",
            "employment_mode",
            "engine_version",
            "composition",
            "candidate_weeks_min",
            "candidate_weeks_max",
            "observed_weeks",
        }
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise ValueError(
                "Calibration CSV missing columns: "
                + ", ".join(missing)
            )

        for row_number, row in enumerate(reader, start=2):
            try:
                saved = upsert_calibration_case(row)
            except Exception as exc:
                raise ValueError(
                    f"Invalid calibration row {row_number}: {exc}"
                ) from exc

            imported += 1
            case_ids.append(saved["case_id"])

    return {
        "schema_version": CALIBRATION_SCHEMA_VERSION,
        "source_path": str(source_path),
        "imported_count": imported,
        "case_ids": case_ids,
    }


def calibration_status() -> dict:
    con = sqlite3.connect(settings.sqlite_path)
    con.row_factory = sqlite3.Row

    try:
        try:
            rows = con.execute(
                """
                SELECT
                    case_id,
                    country_iso3,
                    employment_mode,
                    engine_version,
                    composition,
                    candidate_weeks_min,
                    candidate_weeks_max,
                    observed_weeks,
                    source_label,
                    observed_at,
                    imported_at
                FROM ttv_calibration_cases
                ORDER BY imported_at, case_id
                """
            ).fetchall()
        except sqlite3.OperationalError as exc:
            if "no such table" not in str(exc).lower():
                raise
            return {
                "schema_version": CALIBRATION_SCHEMA_VERSION,
                "infrastructure_ready": False,
                "case_count": 0,
                "country_count": 0,
                "employment_modes": [],
                "engine_versions": [],
                "composition_versions": [],
                "interval_coverage_pct": None,
                "mean_absolute_midpoint_error_weeks": None,
                "mean_signed_midpoint_error_weeks": None,
                "externally_calibrated": False,
                "notes": [
                    "Calibration datastore has not been initialized.",
                ],
            }
    finally:
        con.close()

    cases = [dict(row) for row in rows]
    if not cases:
        return {
            "schema_version": CALIBRATION_SCHEMA_VERSION,
            "infrastructure_ready": True,
            "case_count": 0,
            "country_count": 0,
            "employment_modes": [],
            "engine_versions": [],
            "composition_versions": [],
            "interval_coverage_pct": None,
            "mean_absolute_midpoint_error_weeks": None,
            "mean_signed_midpoint_error_weeks": None,
            "externally_calibrated": False,
            "notes": [
                "Calibration infrastructure is available but contains no observed cases.",
                "No TTV validation gate is satisfied merely by enabling the calibration store.",
            ],
        }

    covered = 0
    absolute_errors = []
    signed_errors = []

    for case in cases:
        lower = float(case["candidate_weeks_min"])
        upper = float(case["candidate_weeks_max"])
        observed = float(case["observed_weeks"])
        midpoint = (lower + upper) / 2.0

        if lower <= observed <= upper:
            covered += 1

        signed_error = midpoint - observed
        signed_errors.append(signed_error)
        absolute_errors.append(abs(signed_error))

    return {
        "schema_version": CALIBRATION_SCHEMA_VERSION,
        "infrastructure_ready": True,
        "case_count": len(cases),
        "country_count": len(
            {case["country_iso3"] for case in cases}
        ),
        "employment_modes": sorted(
            {case["employment_mode"] for case in cases}
        ),
        "engine_versions": sorted(
            {case["engine_version"] for case in cases}
        ),
        "composition_versions": sorted(
            {case["composition"] for case in cases}
        ),
        "interval_coverage_pct": round(
            covered / len(cases) * 100.0,
            2,
        ),
        "mean_absolute_midpoint_error_weeks": round(
            sum(absolute_errors) / len(absolute_errors),
            2,
        ),
        "mean_signed_midpoint_error_weeks": round(
            sum(signed_errors) / len(signed_errors),
            2,
        ),
        "externally_calibrated": False,
        "notes": [
            "Metrics describe observed calibration cases only.",
            "AUGUR does not define a pass/fail threshold until a calibration protocol and representative dataset are approved.",
            "Observed cases contain no full personal profile payload in the calibration store.",
        ],
    }
