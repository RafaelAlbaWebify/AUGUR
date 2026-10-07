from __future__ import annotations

import csv
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


CALIBRATION_SCHEMA_VERSION = "ttv-calibration-v1"
CALIBRATION_PROTOCOL_STATE = "draft_not_approved"
CALIBRATION_PROTOCOL_VERSION = None
CALIBRATION_PROTOCOL_DOCUMENT = "docs/TTV_CALIBRATION_PROTOCOL.md"
CALIBRATION_START_EVENT_DEFINITION_VERSION = None
CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION = None
CALIBRATION_INCLUSION_EXCLUSION_RULES_VERSION = None
CALIBRATION_ACCEPTANCE_CRITERIA_VERSION = None
SUPPORTED_EMPLOYMENT_MODES = {"remote", "local"}
SUPPORTED_SAMPLE_ROLES = {"development", "holdout"}
SUPPORTED_COMPOSITIONS = {"critical_path_v1"}
CALIBRATION_STAGE_IDS = {
    "legal",
    "language",
    "skills",
    "employment",
    "financial",
}

TTV_V1_CALIBRATION_SCOPE = {
    "scope_id": "ttv-estimation-scope-v1",
    "employment_modes": ["remote"],
    "engine_versions": ["ttv-temporal-evidence-v1"],
    "composition_versions": ["critical_path_v1"],
    "notes": [
        "TTV v1 calibration is limited to the same bounded estimation scope as the candidate model.",
        "Local-employment cases may remain useful development evidence but cannot validate the remote-only v1 holdout.",
    ],
}


def calibration_case_scope_status(case: dict) -> dict:
    blockers = []

    employment_mode = str(case.get("employment_mode") or "").strip().lower()
    engine_version = str(case.get("engine_version") or "").strip()
    composition = str(case.get("composition") or "").strip()

    if employment_mode not in TTV_V1_CALIBRATION_SCOPE["employment_modes"]:
        blockers.append("employment_mode_outside_ttv_v1_scope")
    if engine_version not in TTV_V1_CALIBRATION_SCOPE["engine_versions"]:
        blockers.append("engine_version_outside_ttv_v1_scope")
    if composition not in TTV_V1_CALIBRATION_SCOPE["composition_versions"]:
        blockers.append("composition_outside_ttv_v1_scope")

    return {
        "scope_id": TTV_V1_CALIBRATION_SCOPE["scope_id"],
        "eligible_for_v1_holdout": not blockers,
        "blockers": blockers,
    }


def calibration_batch_preflight(cases: list[dict]) -> dict:
    rows = []
    for case in cases:
        case_id = str(case.get("case_id") or "").strip() or None
        scope = calibration_case_scope_status(case)
        rows.append({
            "case_id": case_id,
            **scope,
        })

    eligible = [
        row for row in rows
        if row["eligible_for_v1_holdout"]
    ]

    return {
        "scope": TTV_V1_CALIBRATION_SCOPE,
        "case_count": len(rows),
        "eligible_case_count": len(eligible),
        "ineligible_case_count": len(rows) - len(eligible),
        "all_cases_eligible": len(rows) == len(eligible),
        "cases": rows,
    }


def calibration_protocol_readiness() -> dict:
    requirements = {
        "protocol_version": {
            "ready": CALIBRATION_PROTOCOL_VERSION is not None,
            "version": CALIBRATION_PROTOCOL_VERSION,
        },
        "start_event_definition": {
            "ready": CALIBRATION_START_EVENT_DEFINITION_VERSION is not None,
            "version": CALIBRATION_START_EVENT_DEFINITION_VERSION,
        },
        "viability_outcome_definition": {
            "ready": CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION is not None,
            "version": CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION,
        },
        "inclusion_exclusion_rules": {
            "ready": CALIBRATION_INCLUSION_EXCLUSION_RULES_VERSION is not None,
            "version": CALIBRATION_INCLUSION_EXCLUSION_RULES_VERSION,
        },
        "acceptance_criteria": {
            "ready": CALIBRATION_ACCEPTANCE_CRITERIA_VERSION is not None,
            "version": CALIBRATION_ACCEPTANCE_CRITERIA_VERSION,
        },
    }

    blockers = [
        requirement_id
        for requirement_id, item in requirements.items()
        if not item["ready"]
    ]

    return {
        "protocol_state": CALIBRATION_PROTOCOL_STATE,
        "protocol_document": CALIBRATION_PROTOCOL_DOCUMENT,
        "requirements": requirements,
        "blockers": blockers,
        "ready_for_holdout_collection": len(blockers) == 0,
        "holdout_scope": TTV_V1_CALIBRATION_SCOPE,
    }


def _as_float(value, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc

    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")

    return result


def _normalize_stage_timings(value) -> dict:
    if value in (None, "", {}):
        return {}

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "stage_timings_json must be valid JSON"
            ) from exc

    if not isinstance(value, dict):
        raise ValueError("stage_timings_json must be an object")

    normalized = {}
    for stage_id, stage in value.items():
        if stage_id not in CALIBRATION_STAGE_IDS:
            raise ValueError(
                f"unsupported calibration stage: {stage_id}"
            )
        if not isinstance(stage, dict):
            raise ValueError(
                f"stage {stage_id} must be an object"
            )

        candidate_min = stage.get("candidate_weeks_min")
        candidate_max = stage.get("candidate_weeks_max")
        observed = stage.get("observed_weeks")

        if (
            candidate_min is None
            and candidate_max is None
            and observed is None
        ):
            continue

        if (
            candidate_min is None
            or candidate_max is None
            or observed is None
        ):
            raise ValueError(
                f"stage {stage_id} requires candidate min/max and observed weeks"
            )

        candidate_min = _as_float(
            candidate_min,
            f"{stage_id}.candidate_weeks_min",
        )
        candidate_max = _as_float(
            candidate_max,
            f"{stage_id}.candidate_weeks_max",
        )
        observed = _as_float(
            observed,
            f"{stage_id}.observed_weeks",
        )

        if candidate_min < 0:
            raise ValueError(
                f"{stage_id}.candidate_weeks_min must be >= 0"
            )
        if candidate_max < candidate_min:
            raise ValueError(
                f"{stage_id}.candidate_weeks_max must be >= candidate minimum"
            )
        if observed < 0:
            raise ValueError(
                f"{stage_id}.observed_weeks must be >= 0"
            )

        normalized[stage_id] = {
            "candidate_weeks_min": candidate_min,
            "candidate_weeks_max": candidate_max,
            "observed_weeks": observed,
        }

    return normalized


def validate_calibration_case(case: dict) -> dict:
    case_id = str(case.get("case_id") or "").strip()
    country_iso3 = str(case.get("country_iso3") or "").strip().upper()
    employment_mode = str(case.get("employment_mode") or "").strip().lower()
    engine_version = str(case.get("engine_version") or "").strip()
    composition = str(case.get("composition") or "").strip()
    sample_role = str(
        case.get("sample_role") or "development"
    ).strip().lower()
    start_event_definition_version = str(
        case.get("start_event_definition_version") or ""
    ).strip() or None
    viability_outcome_definition_version = str(
        case.get("viability_outcome_definition_version") or ""
    ).strip() or None

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
    if sample_role not in SUPPORTED_SAMPLE_ROLES:
        raise ValueError(
            "sample_role must be one of: "
            + ", ".join(sorted(SUPPORTED_SAMPLE_ROLES))
        )
    if sample_role == "holdout" and CALIBRATION_PROTOCOL_VERSION is None:
        raise ValueError(
            "holdout cases require an approved calibration protocol version"
        )
    if sample_role == "holdout":
        if not start_event_definition_version:
            raise ValueError(
                "holdout cases require start_event_definition_version"
            )
        if not viability_outcome_definition_version:
            raise ValueError(
                "holdout cases require viability_outcome_definition_version"
            )
        scope = calibration_case_scope_status(case)
        if not scope["eligible_for_v1_holdout"]:
            raise ValueError(
                "holdout case outside TTV v1 calibration scope: "
                + ", ".join(scope["blockers"])
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
    stage_timings = _normalize_stage_timings(
        case.get("stage_timings_json")
        if "stage_timings_json" in case
        else case.get("stage_timings")
    )

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
        "sample_role": sample_role,
        "start_event_definition_version": start_event_definition_version,
        "viability_outcome_definition_version": viability_outcome_definition_version,
        "stage_timings": stage_timings,
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
                sample_role,
                start_event_definition_version,
                viability_outcome_definition_version,
                stage_timings_json,
                imported_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                normalized["sample_role"],
                normalized["start_event_definition_version"],
                normalized["viability_outcome_definition_version"],
                json.dumps(
                    normalized["stage_timings"],
                    sort_keys=True,
                ),
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
        "protocol_state": CALIBRATION_PROTOCOL_STATE,
        "protocol_version": CALIBRATION_PROTOCOL_VERSION,
        "protocol_document": CALIBRATION_PROTOCOL_DOCUMENT,
        "source_path": str(source_path),
        "imported_count": imported,
        "case_ids": case_ids,
    }


def _case_interval_metrics(cases: list[dict]) -> dict:
    if not cases:
        return {
            "case_count": 0,
            "interval_coverage_pct": None,
            "mean_absolute_midpoint_error_weeks": None,
            "mean_signed_midpoint_error_weeks": None,
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
        "case_count": len(cases),
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
    }


def calibration_status() -> dict:
    protocol_readiness = calibration_protocol_readiness()
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
                    sample_role,
                    start_event_definition_version,
                    viability_outcome_definition_version,
                    stage_timings_json,
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
                "protocol_state": CALIBRATION_PROTOCOL_STATE,
                "protocol_version": CALIBRATION_PROTOCOL_VERSION,
                "protocol_document": CALIBRATION_PROTOCOL_DOCUMENT,
                "protocol_readiness": protocol_readiness,
                "infrastructure_ready": False,
                "case_count": 0,
                "country_count": 0,
                "employment_modes": [],
                "engine_versions": [],
                "composition_versions": [],
                "sample_roles": [],
                "start_event_definition_versions": [],
                "viability_outcome_definition_versions": [],
                "development_case_count": 0,
                "holdout_case_count": 0,
                "protocol_ready_for_holdout": CALIBRATION_PROTOCOL_VERSION is not None,
                "interval_coverage_pct": None,
                "mean_absolute_midpoint_error_weeks": None,
                "mean_signed_midpoint_error_weeks": None,
                "stage_metrics": {},
                "sample_role_metrics": {},
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
            "protocol_state": CALIBRATION_PROTOCOL_STATE,
            "protocol_version": CALIBRATION_PROTOCOL_VERSION,
            "protocol_document": CALIBRATION_PROTOCOL_DOCUMENT,
            "protocol_readiness": protocol_readiness,
            "infrastructure_ready": True,
            "case_count": 0,
            "country_count": 0,
            "employment_modes": [],
            "engine_versions": [],
            "composition_versions": [],
            "sample_roles": [],
            "start_event_definition_versions": [],
            "viability_outcome_definition_versions": [],
            "development_case_count": 0,
            "holdout_case_count": 0,
            "protocol_ready_for_holdout": CALIBRATION_PROTOCOL_VERSION is not None,
            "interval_coverage_pct": None,
            "mean_absolute_midpoint_error_weeks": None,
            "mean_signed_midpoint_error_weeks": None,
            "stage_metrics": {},
            "sample_role_metrics": {},
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

    sample_role_metrics = {
        role: _case_interval_metrics(
            [
                case
                for case in cases
                if case["sample_role"] == role
            ]
        )
        for role in sorted(SUPPORTED_SAMPLE_ROLES)
    }

    stage_metrics = {}
    for stage_id in sorted(CALIBRATION_STAGE_IDS):
        stage_rows = []
        for case in cases:
            raw = case.get("stage_timings_json") or "{}"
            try:
                stage_timings = json.loads(raw)
            except json.JSONDecodeError:
                continue
            stage = stage_timings.get(stage_id)
            if stage:
                stage_rows.append(stage)

        if not stage_rows:
            continue

        covered_stage = 0
        absolute_stage_errors = []
        signed_stage_errors = []

        for stage in stage_rows:
            lower = float(stage["candidate_weeks_min"])
            upper = float(stage["candidate_weeks_max"])
            observed = float(stage["observed_weeks"])
            midpoint = (lower + upper) / 2.0

            if lower <= observed <= upper:
                covered_stage += 1

            signed_error = midpoint - observed
            signed_stage_errors.append(signed_error)
            absolute_stage_errors.append(abs(signed_error))

        stage_metrics[stage_id] = {
            "case_count": len(stage_rows),
            "interval_coverage_pct": round(
                covered_stage / len(stage_rows) * 100.0,
                2,
            ),
            "mean_absolute_midpoint_error_weeks": round(
                sum(absolute_stage_errors)
                / len(absolute_stage_errors),
                2,
            ),
            "mean_signed_midpoint_error_weeks": round(
                sum(signed_stage_errors)
                / len(signed_stage_errors),
                2,
            ),
        }

    return {
        "schema_version": CALIBRATION_SCHEMA_VERSION,
        "protocol_state": CALIBRATION_PROTOCOL_STATE,
        "protocol_version": CALIBRATION_PROTOCOL_VERSION,
        "protocol_document": CALIBRATION_PROTOCOL_DOCUMENT,
        "protocol_readiness": protocol_readiness,
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
        "sample_roles": sorted(
            {case["sample_role"] for case in cases}
        ),
        "start_event_definition_versions": sorted(
            {
                case["start_event_definition_version"]
                for case in cases
                if case["start_event_definition_version"]
            }
        ),
        "viability_outcome_definition_versions": sorted(
            {
                case["viability_outcome_definition_version"]
                for case in cases
                if case["viability_outcome_definition_version"]
            }
        ),
        "development_case_count": sum(
            1 for case in cases
            if case["sample_role"] == "development"
        ),
        "holdout_case_count": sum(
            1 for case in cases
            if case["sample_role"] == "holdout"
        ),
        "protocol_ready_for_holdout": CALIBRATION_PROTOCOL_VERSION is not None,
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
        "stage_metrics": stage_metrics,
        "sample_role_metrics": sample_role_metrics,
        "externally_calibrated": False,
        "notes": [
            "Metrics describe observed calibration cases only.",
            "AUGUR does not define a pass/fail threshold until a calibration protocol and representative dataset are approved.",
            "Observed cases contain no full personal profile payload in the calibration store.",
        ],
    }
