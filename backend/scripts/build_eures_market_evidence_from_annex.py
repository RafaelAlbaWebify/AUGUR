from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import settings
from app.db.bootstrap import initialize_datastores
from app.ingestion.eures_annex_pdf import (
    DEFAULT_EURES_ANNEX_URL,
    download_eures_annex,
    extract_eures_annex_rows_from_pdf,
    write_normalized_annex_csv,
)
from app.services.eures_evidence_builder import (
    build_eures_unit_group_evidence_from_csv,
    build_eures_manifest_candidate_from_files,
    write_eures_review_artifact,
)


DEFAULT_EVIDENCE_ID = "eures_shortages_surpluses_2025_annex"
DEFAULT_RULE_VERSION = "EURES_SHORTAGES_SURPLUSES_2025_ANNEX"
DEFAULT_REPORT_YEAR = 2026
DEFAULT_CONDITIONS_YEAR = 2025


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download/extract the official ELA 2025 shortages/surpluses "
            "annex and build an ESCO-reviewed AUGUR evidence artifact."
        )
    )
    parser.add_argument(
        "--pdf",
        help="Use an existing local Annex PDF instead of downloading it.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_EURES_ANNEX_URL,
    )
    parser.add_argument(
        "--normalized-output",
        default=str(
            settings.project_root
            / "exports"
            / "eures_2025_annex_normalized.csv"
        ),
    )
    parser.add_argument(
        "--review-output",
        default=str(
            settings.project_root
            / "exports"
            / "eures_market_review.json"
        ),
    )
    parser.add_argument(
        "--candidate-output",
        default=str(
            settings.project_root
            / "exports"
            / "eures_manifest_candidate.json"
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

    if args.pdf:
        pdf_path = Path(args.pdf).expanduser().resolve()
    else:
        pdf_path = (
            settings.data_dir
            / "cache"
            / "eures_shortages_surpluses_2025_annex.pdf"
        )
        download_eures_annex(
            pdf_path,
            url=args.url,
        )

    rows, extraction = extract_eures_annex_rows_from_pdf(
        pdf_path,
    )
    normalized_path = write_normalized_annex_csv(
        rows,
        args.normalized_output,
    )

    print("AUGUR EURES ANNEX EXTRACTION")
    print("=" * 72)
    print(f"pdf: {pdf_path}")
    print(f"normalized_csv: {normalized_path}")
    print(
        "extraction: "
        f"rows={extraction['row_count']} "
        f"tables={extraction['table_count']} "
        f"pages_with_rows={extraction['pages_with_rows']} "
        f"duplicate_conflicts={extraction['duplicate_conflict_count']}"
    )

    extraction_report = (
        settings.project_root
        / "exports"
        / "eures_2025_annex_extraction.json"
    )
    extraction_report.parent.mkdir(parents=True, exist_ok=True)
    extraction_report.write_text(
        json.dumps(extraction, indent=2, default=str)
        + "\n",
        encoding="utf-8",
    )
    print(f"extraction_report: {extraction_report}")

    if not extraction["ready_for_esco_review"]:
        print()
        print(
            "Extraction is not ready for ESCO review. "
            "Production evidence was not changed."
        )
        return 2

    source_metadata = {
        "evidence_id": DEFAULT_EVIDENCE_ID,
        "rule_version": DEFAULT_RULE_VERSION,
        "report_year": DEFAULT_REPORT_YEAR,
        "conditions_year": DEFAULT_CONDITIONS_YEAR,
        "report_url": args.url,
    }
    review = build_eures_unit_group_evidence_from_csv(
        normalized_path,
        source_metadata=source_metadata,
        threshold=args.threshold,
        min_margin=args.min_margin,
    )
    review_path = write_eures_review_artifact(
        review,
        Path(args.review_output),
    )

    print()
    print("AUGUR EURES ESCO REVIEW")
    print("=" * 72)
    print(f"review_output: {review_path}")
    print(f"resolved_count: {review['resolved_count']}")
    print(f"unresolved_count: {review['unresolved_count']}")
    print(f"ready_for_review: {review['ready_for_review']}")
    print(f"esco_version: {review['esco_version']}")

    if review["unresolved"]:
        print("unresolved:")
        for item in review["unresolved"]:
            print(
                f"  row {item['row_number']}: "
                f"{item.get('occupation_label')!r} "
                f"({item['reason']})"
            )

    if not review["ready_for_review"]:
        print()
        print(
            "Review contains unresolved rows. "
            "Production evidence was not changed and no manifest candidate was generated."
        )
        return 2

    manifest_path = (
        settings.project_root
        / "backend"
        / "app"
        / "evidence"
        / "eures_lmi_2025.json"
    )
    candidate = build_eures_manifest_candidate_from_files(
        review_path,
        manifest_path,
    )
    candidate_path = Path(args.candidate_output).expanduser().resolve()
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(
        json.dumps(
            candidate["candidate_manifest"],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    delta = candidate["comparison"]
    print()
    print("AUGUR EURES MANIFEST CANDIDATE")
    print("=" * 72)
    print(f"candidate_output: {candidate_path}")
    print(
        "coverage: "
        f"current={delta['current_unit_group_count']} "
        f"candidate={delta['candidate_unit_group_count']}"
    )
    print(
        "delta: "
        f"added={len(delta['added_unit_groups'])} "
        f"removed={len(delta['removed_unit_groups'])} "
        f"changed_existing={len(delta['changed_existing_unit_groups'])}"
    )

    print()
    print(
        "NOTE: extraction, ESCO review and candidate preparation never modify "
        "backend/app/evidence/eures_lmi_2025.json automatically."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
