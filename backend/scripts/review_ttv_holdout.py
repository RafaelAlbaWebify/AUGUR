from __future__ import annotations

import argparse

from app.db.bootstrap import initialize_datastores
from app.services.ttv_calibration import (
    calibration_status,
    record_holdout_review,
)


def _yes_no(value: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"yes", "true", "1"}:
        return True
    if normalized in {"no", "false", "0"}:
        return False
    raise argparse.ArgumentTypeError("expected yes/no")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Record the immutable representativeness/cohort review "
            "for the sealed TTV holdout."
        )
    )
    parser.add_argument(
        "--representative",
        required=True,
        type=_yes_no,
        help="Whether the sealed holdout is judged representative.",
    )
    parser.add_argument(
        "--cohort-coverage-adequate",
        required=True,
        type=_yes_no,
        help="Whether the sealed holdout has adequate cohort coverage.",
    )
    parser.add_argument("--reviewer-label")
    parser.add_argument("--notes")
    args = parser.parse_args()

    initialize_datastores()
    review = record_holdout_review(
        representative=args.representative,
        cohort_coverage_adequate=args.cohort_coverage_adequate,
        reviewer_label=args.reviewer_label,
        notes=args.notes,
    )
    status = calibration_status()

    print("AUGUR TTV HOLDOUT REVIEW")
    print("=" * 72)
    print(f"protocol_version: {review['protocol_version']}")
    print(f"holdout_sha256: {review['holdout_sha256']}")
    print(f"representative: {review['representative']}")
    print(
        "cohort_coverage_adequate: "
        f"{review['cohort_coverage_adequate']}"
    )
    print(f"reviewed_at: {review['reviewed_at']}")
    print(
        "ready_for_temporal_model_version: "
        f"{status['activation_readiness']['ready_for_temporal_model_version']}"
    )
    print(
        "NOTE: this review does not assign TEMPORAL_MODEL_VERSION. "
        "A model release remains an explicit versioned change."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
