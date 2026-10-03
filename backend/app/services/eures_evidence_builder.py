from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Callable

from app.esco_store import esco_status, search_occupations


DEFAULT_MATCH_THRESHOLD = 0.84
DEFAULT_MIN_MARGIN = 0.08


def _country_codes(value: str | None) -> list[str]:
    if not value:
        return []

    parts = re.split(r"[,;|\s]+", value.strip().upper())
    result = []

    for part in parts:
        if not part:
            continue
        if len(part) != 2 or not part.isalpha():
            raise ValueError(
                f"Invalid EURES country code: {part!r}"
            )
        if part not in result:
            result.append(part)

    return result


def resolve_eures_occupation(
    occupation_label: str,
    *,
    search: Callable[[str, int], list[dict]] = search_occupations,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
    min_margin: float = DEFAULT_MIN_MARGIN,
) -> dict:
    label = occupation_label.strip()
    if not label:
        return {
            "status": "unresolved",
            "reason": "occupation_label_missing",
            "occupation_label": occupation_label,
            "candidates": [],
        }

    candidates = search(label, 5)
    if not candidates:
        return {
            "status": "unresolved",
            "reason": "no_esco_candidate",
            "occupation_label": label,
            "candidates": [],
        }

    selected = candidates[0]
    score = float(selected.get("match_score") or 0.0)
    second_score = (
        float(candidates[1].get("match_score") or 0.0)
        if len(candidates) > 1
        else 0.0
    )
    margin = score - second_score

    raw_isco = str(
        selected.get("isco_group")
        or selected.get("code")
        or ""
    )
    digits = "".join(
        character
        for character in raw_isco
        if character.isdigit()
    )

    summary_candidates = [
        {
            "preferred_label": item.get("preferred_label"),
            "isco_group": item.get("isco_group"),
            "match_score": item.get("match_score"),
            "match_method": item.get("match_method"),
        }
        for item in candidates[:3]
    ]

    if score < threshold:
        return {
            "status": "unresolved",
            "reason": "match_below_threshold",
            "occupation_label": label,
            "best_score": score,
            "required_score": threshold,
            "candidates": summary_candidates,
        }

    exactish = selected.get("match_method") in {
        "exact_label",
        "label_contains",
    }
    if not exactish and len(candidates) > 1 and margin < min_margin:
        return {
            "status": "unresolved",
            "reason": "ambiguous_esco_match",
            "occupation_label": label,
            "best_score": score,
            "second_score": second_score,
            "margin": round(margin, 4),
            "required_margin": min_margin,
            "candidates": summary_candidates,
        }

    if len(digits) < 4:
        return {
            "status": "unresolved",
            "reason": "esco_match_has_no_isco_unit_group",
            "occupation_label": label,
            "best_score": score,
            "candidates": summary_candidates,
        }

    return {
        "status": "resolved",
        "occupation_label": label,
        "isco_unit": digits[:4],
        "esco_label": selected.get("preferred_label"),
        "match_score": score,
        "match_method": selected.get("match_method"),
        "match_margin": round(margin, 4),
        "candidates": summary_candidates,
    }


def build_eures_unit_group_evidence(
    rows: list[dict],
    *,
    source_metadata: dict,
    search: Callable[[str, int], list[dict]] = search_occupations,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
    min_margin: float = DEFAULT_MIN_MARGIN,
) -> dict:
    resolved: dict[str, dict] = {}
    unresolved: list[dict] = []

    for row_number, row in enumerate(rows, start=2):
        occupation_label = str(
            row.get("occupation_label")
            or row.get("occupation")
            or ""
        ).strip()

        resolution = resolve_eures_occupation(
            occupation_label,
            search=search,
            threshold=threshold,
            min_margin=min_margin,
        )

        if resolution["status"] != "resolved":
            unresolved.append(
                {
                    "row_number": row_number,
                    **resolution,
                }
            )
            continue

        isco_unit = resolution["isco_unit"]
        if isco_unit in resolved:
            unresolved.append(
                {
                    "row_number": row_number,
                    "status": "unresolved",
                    "reason": "duplicate_isco_unit",
                    "occupation_label": occupation_label,
                    "isco_unit": isco_unit,
                    "existing_occupation_label": resolved[
                        isco_unit
                    ]["occupation_label"],
                    "candidates": resolution["candidates"],
                }
            )
            continue

        try:
            shortages = _country_codes(
                row.get("shortage_countries")
            )
            surpluses = _country_codes(
                row.get("surplus_countries")
            )
        except ValueError as exc:
            unresolved.append(
                {
                    "row_number": row_number,
                    "status": "unresolved",
                    "reason": "invalid_country_codes",
                    "occupation_label": occupation_label,
                    "error": str(exc),
                    "candidates": resolution["candidates"],
                }
            )
            continue

        resolved[isco_unit] = {
            "occupation_label": occupation_label,
            "esco_label": resolution["esco_label"],
            "match_score": resolution["match_score"],
            "match_method": resolution["match_method"],
            "shortage_countries": shortages,
            "surplus_countries": surpluses,
        }

    return {
        "builder_version": "eures-esco-resolver-v1",
        "source_metadata": source_metadata,
        "matching": {
            "threshold": threshold,
            "min_margin": min_margin,
            "requires_full_esco": True,
        },
        "resolved_count": len(resolved),
        "unresolved_count": len(unresolved),
        "unit_group_signals": dict(
            sorted(resolved.items())
        ),
        "unresolved": unresolved,
        "ready_for_review": len(unresolved) == 0,
        "notes": [
            "This artifact is a review candidate and does not modify AUGUR's production EURES manifest.",
            "Every resolved row records the ESCO label and match score used to assign an ISCO unit group.",
            "Unresolved or ambiguous rows must be reviewed rather than silently guessed.",
        ],
    }


def build_eures_unit_group_evidence_from_csv(
    path: str | Path,
    *,
    source_metadata: dict,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
    min_margin: float = DEFAULT_MIN_MARGIN,
    search: Callable[[str, int], list[dict]] | None = None,
) -> dict:
    status = esco_status()
    if status["mode"] != "full":
        raise RuntimeError(
            "Full ESCO is required to build EURES unit-group evidence. "
            "Import the official ESCO CSV package first."
        )

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
            "occupation_label",
            "shortage_countries",
            "surplus_countries",
        }
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise ValueError(
                "EURES evidence CSV missing columns: "
                + ", ".join(missing)
            )
        rows = list(reader)

    result = build_eures_unit_group_evidence(
        rows,
        source_metadata=source_metadata,
        search=search or search_occupations,
        threshold=threshold,
        min_margin=min_margin,
    )

    return {
        **result,
        "source_path": str(source_path),
        "esco_version": status["version"],
    }


def write_eures_review_artifact(
    result: dict,
    path: str | Path,
) -> Path:
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return output_path
