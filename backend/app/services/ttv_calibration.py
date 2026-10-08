from __future__ import annotations

import csv
import json
import math
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
from statistics import median

from app.core.config import settings


CALIBRATION_SCHEMA_VERSION = "ttv-calibration-v1"
CALIBRATION_EXCHANGE_VERSION = "ttv-development-exchange-v1"
CALIBRATION_PROTOCOL_STATE = "protocol_v1_frozen_holdout_collection_enabled"
CALIBRATION_PROTOCOL_VERSION = "ttv-calibration-protocol-v1"
CALIBRATION_PROTOCOL_DOCUMENT = "docs/TTV_CALIBRATION_PROTOCOL.md"
CALIBRATION_START_EVENT_DEFINITION_VERSION = "ttv-start-active-language-transition-v1"
CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION = "ttv-outcome-b2-remote-viability-v1"
CALIBRATION_INCLUSION_EXCLUSION_RULES_VERSION = "ttv-inclusion-remote-scope-v1"
CALIBRATION_ACCEPTANCE_CRITERIA_VERSION = "ttv-acceptance-criteria-v1"

CALIBRATION_ACCEPTANCE_CRITERIA = {
    "minimum_holdout_cases": 60,
    "minimum_interval_coverage_pct": 80.0,
    "maximum_median_interval_width_weeks": 20.0,
    "maximum_mean_absolute_midpoint_error_weeks": 8.0,
    "maximum_absolute_mean_signed_midpoint_error_weeks": 4.0,
    "maximum_mean_miss_distance_weeks": 6.0,
    "maximum_below_interval_rate_pct": 15.0,
    "maximum_above_interval_rate_pct": 15.0,
    "minimum_cases_for_cohort_claim": 15,
    "notes": [
        "These are pre-declared product acceptance thresholds, not thresholds fitted to development or holdout outcomes.",
        "Cohort-specific pass/fail claims require at least 15 holdout cases in that cohort.",
        "Representative-sample review remains a separate gate and cannot be inferred from sample size alone.",
    ],
}
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

TTV_OUTCOME_EVIDENCE_TYPES = {
    "official_exam",
    "cefr_aligned_assessment",
    "course_certificate",
    "other_documented",
}

TTV_OUTCOME_CEFR_LEVELS = {"B2", "C1", "C2"}


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
        "acceptance_criteria": CALIBRATION_ACCEPTANCE_CRITERIA,
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


def _normalize_calibration_context(value) -> dict:
    if value in (None, "", {}):
        return {}

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "context_json must be valid JSON"
            ) from exc

    if not isinstance(value, dict):
        raise ValueError("calibration context must be an object")

    allowed_cefr = {"A1", "A2", "B1", "B2", "C1", "C2"}
    normalized = {}

    scope_id = str(value.get("scope_id") or "").strip()
    if scope_id:
        normalized["scope_id"] = scope_id

    for field in ("current_cefr", "target_cefr", "achieved_cefr"):
        raw = str(value.get(field) or "").strip().upper()
        if raw:
            if raw not in allowed_cefr:
                raise ValueError(f"{field} must be a CEFR level")
            if (
                field == "achieved_cefr"
                and raw not in TTV_OUTCOME_CEFR_LEVELS
            ):
                raise ValueError(
                    "achieved_cefr must be B2, C1 or C2"
                )
            normalized[field] = raw

    outcome_evidence_type = str(
        value.get("outcome_evidence_type") or ""
    ).strip().lower()
    if outcome_evidence_type:
        if outcome_evidence_type not in TTV_OUTCOME_EVIDENCE_TYPES:
            raise ValueError("outcome_evidence_type is not supported")
        normalized["outcome_evidence_type"] = outcome_evidence_type

    weekly = value.get("weekly_study_hours")
    if weekly not in (None, ""):
        weekly = _as_float(weekly, "weekly_study_hours")
        if not (0 < weekly <= 80):
            raise ValueError("weekly_study_hours must be > 0 and <= 80")
        normalized["weekly_study_hours"] = weekly

    guided_min = value.get("guided_hours_min")
    guided_max = value.get("guided_hours_max")
    if guided_min not in (None, "") or guided_max not in (None, ""):
        if guided_min in (None, "") or guided_max in (None, ""):
            raise ValueError(
                "guided_hours_min and guided_hours_max must be supplied together"
            )
        guided_min = _as_float(guided_min, "guided_hours_min")
        guided_max = _as_float(guided_max, "guided_hours_max")
        if guided_min < 0 or guided_max < guided_min:
            raise ValueError("guided hour range is invalid")
        normalized["guided_hours_min"] = guided_min
        normalized["guided_hours_max"] = guided_max

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
    calibration_protocol_version = str(
        case.get("calibration_protocol_version") or ""
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
    if sample_role == "holdout":
        if CALIBRATION_PROTOCOL_VERSION is None:
            raise ValueError(
                "holdout cases require an approved calibration protocol version"
            )
        if calibration_protocol_version != CALIBRATION_PROTOCOL_VERSION:
            raise ValueError(
                "holdout cases require calibration_protocol_version="
                + CALIBRATION_PROTOCOL_VERSION
            )
        if (
            start_event_definition_version
            != CALIBRATION_START_EVENT_DEFINITION_VERSION
        ):
            raise ValueError(
                "holdout cases require the frozen start-event definition version"
            )
        if (
            viability_outcome_definition_version
            != CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION
        ):
            raise ValueError(
                "holdout cases require the frozen viability-outcome definition version"
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
    context = _normalize_calibration_context(
        case.get("context_json")
        if "context_json" in case
        else case.get("context")
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
        "calibration_protocol_version": calibration_protocol_version,
        "stage_timings": stage_timings,
        "context": context,
    }


def upsert_calibration_case(case: dict) -> dict:
    normalized = validate_calibration_case(case)
    imported_at = datetime.now(timezone.utc).isoformat()

    con = sqlite3.connect(settings.sqlite_path)
    try:
        existing = con.execute(
            """
            SELECT sample_role
            FROM ttv_calibration_cases
            WHERE case_id = ?
            """,
            [normalized["case_id"]],
        ).fetchone()
        if existing is not None and str(existing[0]).lower() == "holdout":
            raise ValueError(
                "holdout calibration cases are immutable once imported"
            )
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
                calibration_protocol_version,
                stage_timings_json,
                context_json,
                imported_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                normalized["calibration_protocol_version"],
                json.dumps(
                    normalized["stage_timings"],
                    sort_keys=True,
                ),
                json.dumps(
                    normalized["context"],
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

        raw_rows = list(reader)

    validated_rows = []
    seen_case_ids = set()
    for row_number, row in enumerate(raw_rows, start=2):
        try:
            normalized = validate_calibration_case(row)
        except Exception as exc:
            raise ValueError(
                f"Invalid calibration row {row_number}: {exc}"
            ) from exc

        case_id = normalized["case_id"]
        if case_id in seen_case_ids:
            raise ValueError(
                f"Invalid calibration row {row_number}: "
                f"duplicate case_id in import batch: {case_id}"
            )
        seen_case_ids.add(case_id)
        validated_rows.append(row)

    imported = 0
    case_ids: list[str] = []
    for row in validated_rows:
        saved = upsert_calibration_case(row)
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

def import_holdout_calibration_csv(path: str | Path) -> dict:
    source_path = Path(path).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    with source_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError("Holdout calibration CSV contains no cases")

    for row_number, row in enumerate(rows, start=2):
        role = str(row.get("sample_role") or "").strip().lower()
        if role != "holdout":
            raise ValueError(
                f"Invalid holdout row {row_number}: sample_role must be holdout"
            )
        if (
            str(row.get("calibration_protocol_version") or "").strip()
            != CALIBRATION_PROTOCOL_VERSION
        ):
            raise ValueError(
                f"Invalid holdout row {row_number}: "
                "calibration_protocol_version must equal "
                + str(CALIBRATION_PROTOCOL_VERSION)
            )
        if (
            str(row.get("start_event_definition_version") or "").strip()
            != CALIBRATION_START_EVENT_DEFINITION_VERSION
        ):
            raise ValueError(
                f"Invalid holdout row {row_number}: "
                "start_event_definition_version does not match the frozen protocol"
            )
        if (
            str(row.get("viability_outcome_definition_version") or "").strip()
            != CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION
        ):
            raise ValueError(
                f"Invalid holdout row {row_number}: "
                "viability_outcome_definition_version does not match the frozen protocol"
            )

    result = import_calibration_csv(source_path)
    return {
        **result,
        "import_mode": "holdout",
        "frozen_protocol_version": CALIBRATION_PROTOCOL_VERSION,
        "acceptance_criteria_version": CALIBRATION_ACCEPTANCE_CRITERIA_VERSION,
    }


def _case_interval_metrics(cases: list[dict]) -> dict:
    if not cases:
        return {
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

    covered = 0
    below = 0
    above = 0
    widths = []
    absolute_errors = []
    signed_errors = []
    miss_distances = []

    for case in cases:
        lower = float(case["candidate_weeks_min"])
        upper = float(case["candidate_weeks_max"])
        observed = float(case["observed_weeks"])
        midpoint = (lower + upper) / 2.0

        widths.append(upper - lower)

        if lower <= observed <= upper:
            covered += 1
        elif observed < lower:
            below += 1
            miss_distances.append(lower - observed)
        else:
            above += 1
            miss_distances.append(observed - upper)

        signed_error = midpoint - observed
        signed_errors.append(signed_error)
        absolute_errors.append(abs(signed_error))

    return {
        "case_count": len(cases),
        "interval_coverage_pct": round(
            covered / len(cases) * 100.0,
            2,
        ),
        "mean_interval_width_weeks": round(
            sum(widths) / len(widths),
            2,
        ),
        "median_interval_width_weeks": round(
            float(median(widths)),
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
        "outside_interval_count": below + above,
        "below_interval_count": below,
        "above_interval_count": above,
        "mean_miss_distance_weeks": (
            round(sum(miss_distances) / len(miss_distances), 2)
            if miss_distances
            else 0.0
        ),
    }


def evaluate_holdout_acceptance(cases: list[dict]) -> dict:
    eligible = [
        case
        for case in cases
        if (
            str(case.get("sample_role") or "").lower() == "holdout"
            and calibration_case_scope_status(case)["eligible_for_v1_holdout"]
        )
    ]
    metrics = _case_interval_metrics(eligible)
    criteria = CALIBRATION_ACCEPTANCE_CRITERIA
    case_count = metrics["case_count"]

    checks = {
        "minimum_holdout_cases": {
            "passed": case_count >= criteria["minimum_holdout_cases"],
            "observed": case_count,
            "threshold": criteria["minimum_holdout_cases"],
            "operator": ">=",
        },
    }

    if case_count:
        below_rate = round(
            metrics["below_interval_count"] / case_count * 100.0,
            2,
        )
        above_rate = round(
            metrics["above_interval_count"] / case_count * 100.0,
            2,
        )
        checks.update({
            "interval_coverage_pct": {
                "passed": (
                    metrics["interval_coverage_pct"]
                    >= criteria["minimum_interval_coverage_pct"]
                ),
                "observed": metrics["interval_coverage_pct"],
                "threshold": criteria["minimum_interval_coverage_pct"],
                "operator": ">=",
            },
            "median_interval_width_weeks": {
                "passed": (
                    metrics["median_interval_width_weeks"]
                    <= criteria["maximum_median_interval_width_weeks"]
                ),
                "observed": metrics["median_interval_width_weeks"],
                "threshold": criteria["maximum_median_interval_width_weeks"],
                "operator": "<=",
            },
            "mean_absolute_midpoint_error_weeks": {
                "passed": (
                    metrics["mean_absolute_midpoint_error_weeks"]
                    <= criteria["maximum_mean_absolute_midpoint_error_weeks"]
                ),
                "observed": metrics["mean_absolute_midpoint_error_weeks"],
                "threshold": criteria["maximum_mean_absolute_midpoint_error_weeks"],
                "operator": "<=",
            },
            "absolute_mean_signed_midpoint_error_weeks": {
                "passed": (
                    abs(metrics["mean_signed_midpoint_error_weeks"])
                    <= criteria["maximum_absolute_mean_signed_midpoint_error_weeks"]
                ),
                "observed": round(
                    abs(metrics["mean_signed_midpoint_error_weeks"]),
                    2,
                ),
                "threshold": criteria["maximum_absolute_mean_signed_midpoint_error_weeks"],
                "operator": "<=",
            },
            "mean_miss_distance_weeks": {
                "passed": (
                    metrics["mean_miss_distance_weeks"]
                    <= criteria["maximum_mean_miss_distance_weeks"]
                ),
                "observed": metrics["mean_miss_distance_weeks"],
                "threshold": criteria["maximum_mean_miss_distance_weeks"],
                "operator": "<=",
            },
            "below_interval_rate_pct": {
                "passed": (
                    below_rate
                    <= criteria["maximum_below_interval_rate_pct"]
                ),
                "observed": below_rate,
                "threshold": criteria["maximum_below_interval_rate_pct"],
                "operator": "<=",
            },
            "above_interval_rate_pct": {
                "passed": (
                    above_rate
                    <= criteria["maximum_above_interval_rate_pct"]
                ),
                "observed": above_rate,
                "threshold": criteria["maximum_above_interval_rate_pct"],
                "operator": "<=",
            },
        })

    sample_ready = case_count >= criteria["minimum_holdout_cases"]
    evaluated_checks = (
        checks.values()
        if sample_ready
        else [checks["minimum_holdout_cases"]]
    )
    passed = sample_ready and all(
        item["passed"]
        for item in evaluated_checks
    )

    return {
        "criteria_version": CALIBRATION_ACCEPTANCE_CRITERIA_VERSION,
        "scope_id": TTV_V1_CALIBRATION_SCOPE["scope_id"],
        "status": (
            "passed"
            if passed
            else "failed"
            if sample_ready
            else "insufficient_sample"
        ),
        "passed": passed,
        "eligible_holdout_case_count": case_count,
        "metrics": metrics,
        "checks": checks,
        "representativeness_review_required": True,
        "notes": [
            "Passing numerical thresholds does not by itself establish sample representativeness.",
            "The final holdout must remain untouched by model design and tuning.",
        ],
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
                    calibration_protocol_version,
                    stage_timings_json,
                    context_json,
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
                "calibration_protocol_versions": [],
                "development_case_count": 0,
                "holdout_case_count": 0,
                "protocol_ready_for_holdout": CALIBRATION_PROTOCOL_VERSION is not None,
                "interval_coverage_pct": None,
                "mean_interval_width_weeks": None,
                "median_interval_width_weeks": None,
                "mean_absolute_midpoint_error_weeks": None,
                "mean_signed_midpoint_error_weeks": None,
                "outside_interval_count": 0,
                "below_interval_count": 0,
                "above_interval_count": 0,
                "mean_miss_distance_weeks": None,
                "stage_metrics": {},
                "sample_role_metrics": {},
                "context_summary": {
                    "context_case_count": 0,
                    "current_cefr_levels": [],
                    "target_cefr_levels": [],
                    "achieved_cefr_levels": [],
                    "outcome_evidence_types": [],
                    "weekly_study_hours": [],
                },
                "holdout_acceptance": evaluate_holdout_acceptance([]),
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
            "calibration_protocol_versions": [],
            "development_case_count": 0,
            "holdout_case_count": 0,
            "protocol_ready_for_holdout": CALIBRATION_PROTOCOL_VERSION is not None,
            "interval_coverage_pct": None,
            "mean_interval_width_weeks": None,
            "median_interval_width_weeks": None,
            "mean_absolute_midpoint_error_weeks": None,
            "mean_signed_midpoint_error_weeks": None,
            "outside_interval_count": 0,
            "below_interval_count": 0,
            "above_interval_count": 0,
            "mean_miss_distance_weeks": None,
            "stage_metrics": {},
            "sample_role_metrics": {},
            "context_summary": {
                "context_case_count": 0,
                "current_cefr_levels": [],
                "target_cefr_levels": [],
                "achieved_cefr_levels": [],
                "outcome_evidence_types": [],
                "weekly_study_hours": [],
            },
            "externally_calibrated": False,
            "notes": [
                "Calibration infrastructure is available but contains no observed cases.",
                "No TTV validation gate is satisfied merely by enabling the calibration store.",
            ],
        }

    overall_metrics = _case_interval_metrics(cases)

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

        stage_metrics[stage_id] = _case_interval_metrics(stage_rows)

    parsed_contexts = []
    for case in cases:
        try:
            parsed = json.loads(case.get("context_json") or "{}")
        except json.JSONDecodeError:
            parsed = {}
        if parsed:
            parsed_contexts.append(parsed)

    context_summary = {
        "context_case_count": len(parsed_contexts),
        "current_cefr_levels": sorted({
            str(item["current_cefr"])
            for item in parsed_contexts
            if item.get("current_cefr")
        }),
        "target_cefr_levels": sorted({
            str(item["target_cefr"])
            for item in parsed_contexts
            if item.get("target_cefr")
        }),
        "achieved_cefr_levels": sorted({
            str(item["achieved_cefr"])
            for item in parsed_contexts
            if item.get("achieved_cefr")
        }),
        "outcome_evidence_types": sorted({
            str(item["outcome_evidence_type"])
            for item in parsed_contexts
            if item.get("outcome_evidence_type")
        }),
        "weekly_study_hours": sorted({
            float(item["weekly_study_hours"])
            for item in parsed_contexts
            if item.get("weekly_study_hours") is not None
        }),
    }

    holdout_acceptance = evaluate_holdout_acceptance(cases)

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
        "calibration_protocol_versions": sorted(
            {
                case["calibration_protocol_version"]
                for case in cases
                if case["calibration_protocol_version"]
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
        **{
            key: value
            for key, value in overall_metrics.items()
            if key != "case_count"
        },
        "stage_metrics": stage_metrics,
        "sample_role_metrics": sample_role_metrics,
        "context_summary": context_summary,
        "holdout_acceptance": holdout_acceptance,
        "externally_calibrated": False,
        "notes": [
            "Metrics describe observed calibration cases only.",
            "Frozen numerical acceptance thresholds are pre-declared, but they do not establish representativeness or external calibration by themselves.",
            "Observed cases contain no full personal profile payload in the calibration store.",
        ],
    }



def _parse_utc_timestamp(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def active_calibration_observation(country_iso3: str) -> dict | None:
    target = country_iso3.strip().upper()
    con = sqlite3.connect(settings.sqlite_path)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            """
            SELECT *
            FROM ttv_calibration_observations
            WHERE country_iso3 = ? AND status = 'active'
            ORDER BY started_at DESC
            LIMIT 1
            """,
            [target],
        ).fetchone()
    finally:
        con.close()

    if row is None:
        return None

    result = dict(row)
    result["baseline"] = json.loads(result.pop("baseline_json") or "{}")
    result["completion"] = json.loads(result.pop("completion_json") or "{}")
    return result


def start_calibration_observation(
    country_iso3: str,
    ttv_result: dict,
) -> dict:
    target = country_iso3.strip().upper()
    temporal = ttv_result.get("temporal_evidence") or {}
    scope = temporal.get("estimation_scope") or {}
    candidate = ttv_result.get("candidate_time_range")
    language = (temporal.get("stages") or {}).get("language") or {}

    if not scope.get("in_scope"):
        raise ValueError(
            "TTV calibration observation requires an in-scope v1 case"
        )
    if not temporal.get("calendar_ready"):
        raise ValueError(
            "TTV calibration observation requires calendar-ready temporal evidence"
        )
    if not candidate:
        raise ValueError(
            "TTV calibration observation requires a candidate range"
        )
    if language.get("weeks_max") in (None, 0):
        raise ValueError(
            "TTV calibration observation requires a non-zero language transition"
        )

    existing = active_calibration_observation(target)
    if existing is not None:
        return existing

    started_at = datetime.now(timezone.utc)
    case_id = f"ttv-dev-{target.lower()}-{uuid4().hex[:12]}"
    baseline = {
        "target_country_iso3": target,
        "scope_id": scope.get("scope_id"),
        "candidate_range": candidate,
        "language": {
            "current_cefr": language.get("current_cefr"),
            "target_cefr": language.get("target_cefr"),
            "guided_hours_min": language.get("guided_hours_min"),
            "guided_hours_max": language.get("guided_hours_max"),
            "weekly_study_hours": language.get("weekly_study_hours"),
            "weeks_min": language.get("weeks_min"),
            "weeks_max": language.get("weeks_max"),
        },
        "start_event_definition_version": CALIBRATION_START_EVENT_DEFINITION_VERSION,
        "viability_outcome_definition_version": CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION,
        "inclusion_exclusion_rules_version": CALIBRATION_INCLUSION_EXCLUSION_RULES_VERSION,
    }

    con = sqlite3.connect(settings.sqlite_path)
    try:
        con.execute(
            """
            INSERT INTO ttv_calibration_observations (
                case_id,
                country_iso3,
                status,
                scope_id,
                engine_version,
                composition,
                candidate_weeks_min,
                candidate_weeks_max,
                started_at,
                baseline_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                case_id,
                target,
                scope.get("scope_id") or TTV_V1_CALIBRATION_SCOPE["scope_id"],
                temporal.get("engine_version") or "ttv-temporal-evidence-v1",
                candidate.get("composition") or "critical_path_v1",
                float(candidate["weeks_min"]),
                float(candidate["weeks_max"]),
                started_at.isoformat(),
                json.dumps(baseline, sort_keys=True),
                started_at.isoformat(),
                started_at.isoformat(),
            ],
        )
        con.commit()
    finally:
        con.close()

    return active_calibration_observation(target)


def complete_calibration_observation(
    case_id: str,
    *,
    achieved_cefr: str,
    evidence_type: str,
    observed_at: str | None = None,
) -> dict:
    con = sqlite3.connect(settings.sqlite_path)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            """
            SELECT *
            FROM ttv_calibration_observations
            WHERE case_id = ?
            """,
            [case_id],
        ).fetchone()
    finally:
        con.close()

    if row is None:
        raise ValueError("TTV calibration observation not found")
    if row["status"] != "active":
        raise ValueError("TTV calibration observation is not active")

    achieved = str(achieved_cefr or "").strip().upper()
    if achieved not in TTV_OUTCOME_CEFR_LEVELS:
        raise ValueError(
            "achieved_cefr must be B2, C1 or C2"
        )

    evidence = str(evidence_type or "").strip().lower()
    if evidence not in TTV_OUTCOME_EVIDENCE_TYPES:
        raise ValueError(
            "evidence_type must describe documented CEFR evidence"
        )

    started = _parse_utc_timestamp(row["started_at"], "started_at")
    completed = (
        _parse_utc_timestamp(observed_at, "observed_at")
        if observed_at
        else datetime.now(timezone.utc)
    )
    if completed < started:
        raise ValueError("observed_at must not be before started_at")

    observed_weeks = round(
        (completed - started).total_seconds() / (7 * 24 * 60 * 60),
        4,
    )
    baseline = json.loads(row["baseline_json"] or "{}")
    language = baseline.get("language") or {}

    case = upsert_calibration_case(
        {
            "case_id": row["case_id"],
            "country_iso3": row["country_iso3"],
            "employment_mode": "remote",
            "engine_version": row["engine_version"],
            "composition": row["composition"],
            "candidate_weeks_min": row["candidate_weeks_min"],
            "candidate_weeks_max": row["candidate_weeks_max"],
            "observed_weeks": observed_weeks,
            "source_label": "local_opt_in_observed_ttv_v1",
            "observed_at": completed.isoformat(),
            "sample_role": "development",
            "start_event_definition_version": CALIBRATION_START_EVENT_DEFINITION_VERSION,
            "viability_outcome_definition_version": CALIBRATION_VIABILITY_OUTCOME_DEFINITION_VERSION,
            "stage_timings": {
                "language": {
                    "candidate_weeks_min": float(language.get("weeks_min") or 0),
                    "candidate_weeks_max": float(language.get("weeks_max") or 0),
                    "observed_weeks": observed_weeks,
                }
            },
            "context": {
                "scope_id": baseline.get("scope_id"),
                "current_cefr": language.get("current_cefr"),
                "target_cefr": language.get("target_cefr"),
                "weekly_study_hours": language.get("weekly_study_hours"),
                "guided_hours_min": language.get("guided_hours_min"),
                "guided_hours_max": language.get("guided_hours_max"),
                "achieved_cefr": achieved,
                "outcome_evidence_type": evidence,
            },
        }
    )

    completion = {
        "outcome": "documented_b2_or_better",
        "achieved_cefr": achieved,
        "evidence_type": evidence,
        "observed_at": completed.isoformat(),
        "observed_weeks": observed_weeks,
        "sample_role": "development",
    }
    now = datetime.now(timezone.utc).isoformat()

    con = sqlite3.connect(settings.sqlite_path)
    try:
        con.execute(
            """
            UPDATE ttv_calibration_observations
            SET status = 'completed',
                completed_at = ?,
                completion_json = ?,
                updated_at = ?
            WHERE case_id = ?
            """,
            [
                completed.isoformat(),
                json.dumps(completion, sort_keys=True),
                now,
                case_id,
            ],
        )
        con.commit()
    finally:
        con.close()

    return {
        "observation": {
            **dict(row),
            "status": "completed",
            "completed_at": completed.isoformat(),
            "baseline": baseline,
            "completion": completion,
        },
        "calibration_case": case,
        "calibration_status": calibration_status(),
    }


def cancel_calibration_observation(case_id: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    con = sqlite3.connect(settings.sqlite_path)
    try:
        cursor = con.execute(
            """
            UPDATE ttv_calibration_observations
            SET status = 'cancelled',
                updated_at = ?
            WHERE case_id = ? AND status = 'active'
            """,
            [now, case_id],
        )
        con.commit()
    finally:
        con.close()

    if cursor.rowcount == 0:
        raise ValueError("Active TTV calibration observation not found")

    return {
        "case_id": case_id,
        "status": "cancelled",
        "updated_at": now,
    }



def export_development_calibration_package() -> dict:
    con = sqlite3.connect(settings.sqlite_path)
    con.row_factory = sqlite3.Row
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
                sample_role,
                start_event_definition_version,
                viability_outcome_definition_version,
                calibration_protocol_version,
                stage_timings_json,
                context_json
            FROM ttv_calibration_cases
            WHERE sample_role = 'development'
            ORDER BY case_id
            """
        ).fetchall()
    finally:
        con.close()

    cases = []
    for row in rows:
        item = dict(row)
        item["stage_timings"] = json.loads(
            item.pop("stage_timings_json") or "{}"
        )
        item["context"] = json.loads(
            item.pop("context_json") or "{}"
        )
        cases.append(item)

    return {
        "exchange_version": CALIBRATION_EXCHANGE_VERSION,
        "schema_version": CALIBRATION_SCHEMA_VERSION,
        "scope_id": TTV_V1_CALIBRATION_SCOPE["scope_id"],
        "privacy": {
            "contains_full_profile": False,
            "contains_name": False,
            "contains_email": False,
            "contains_address": False,
            "contains_free_text_history": False,
        },
        "case_count": len(cases),
        "cases": cases,
        "notes": [
            "Development exchange contains calibration fields only and excludes the personal profile.",
            "Exact observation/import timestamps and local provenance labels are omitted from the exchange package.",
            "Imported development cases remain exploratory and cannot become holdout evidence retrospectively.",
        ],
    }


def import_development_calibration_package(package: dict) -> dict:
    if package.get("exchange_version") != CALIBRATION_EXCHANGE_VERSION:
        raise ValueError("unsupported TTV calibration exchange version")

    raw_cases = package.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("TTV calibration exchange cases must be a list")

    preflight = calibration_batch_preflight(raw_cases)
    imported_case_ids = []

    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            raise ValueError("TTV calibration exchange case must be an object")

        if str(raw_case.get("sample_role") or "development").lower() != "development":
            raise ValueError(
                "TTV development exchange accepts development cases only"
            )

        saved = upsert_calibration_case(
            {
                **raw_case,
                "sample_role": "development",
                "source_label": "anonymized_development_exchange",
                "observed_at": None,
                "stage_timings": raw_case.get("stage_timings") or {},
                "context": raw_case.get("context") or {},
            }
        )
        imported_case_ids.append(saved["case_id"])

    return {
        "exchange_version": CALIBRATION_EXCHANGE_VERSION,
        "imported_count": len(imported_case_ids),
        "case_ids": imported_case_ids,
        "preflight": preflight,
        "calibration_status": calibration_status(),
    }
