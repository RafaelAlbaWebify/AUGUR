from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import settings
from app.db.bootstrap import initialize_datastores
from app.services.eures_evidence_builder import (
    build_eures_unit_group_evidence_from_csv,
    write_eures_review_artifact,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve a normalized EURES occupation table against "
            "the local full ESCO dataset and write a review artifact."
        )
    )
    parser.add_argument(
        "path",
        help=(
            "CSV with occupation_label, shortage_countries and "
            "surplus_countries columns."
        ),
    )
    parser.add_argument(
        "--evidence-id",
        required=True,
    )
    parser.add_argument(
        "--rule-version",
        required=True,
    )
    parser.add_argument(
        "--report-year",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--conditions-year",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--report-url",
        required=True,
    )
    parser.add_argument(
        "--output",
        default=str(
            settings.project_root
            / "exports"
            / "eures_market_review.json"
        ),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.84,
    )
    parser.add_argument(
        "--min-margin",
        type=float,
        default=0.08,
    )
    args = parser.parse_args()

    initialize_datastores()

    source_metadata = {
        "evidence_id": args.evidence_id,
        "rule_version": args.rule_version,
        "report_year": args.report_year,
        "conditions_year": args.conditions_year,
        "report_url": args.report_url,
    }

    result = build_eures_unit_group_evidence_from_csv(
        args.path,
        source_metadata=source_metadata,
        threshold=args.threshold,
        min_margin=args.min_margin,
    )

    output = write_eures_review_artifact(
        result,
        Path(args.output),
    )

    print("AUGUR EURES MARKET EVIDENCE REVIEW")
    print("=" * 72)
    print(f"output: {output}")
    print(f"resolved_count: {result['resolved_count']}")
    print(f"unresolved_count: {result['unresolved_count']}")
    print(f"ready_for_review: {result['ready_for_review']}")
    print(f"esco_version: {result['esco_version']}")

    if result["unresolved"]:
        print("unresolved:")
        for item in result["unresolved"]:
            print(
                f"  row {item['row_number']}: "
                f"{item.get('occupation_label')!r} "
                f"({item['reason']})"
            )

    print()
    print(
        "NOTE: this command never modifies the production "
        "EURES manifest automatically."
    )

    return 0 if result["ready_for_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
