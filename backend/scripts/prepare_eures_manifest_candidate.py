from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import settings
from app.services.eures_evidence_builder import (
    build_eures_manifest_candidate_from_files,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a production-shaped EURES manifest candidate from a "
            "fully resolved review artifact without modifying production."
        )
    )
    parser.add_argument(
        "--review",
        default=str(
            settings.project_root
            / "exports"
            / "eures_market_review.json"
        ),
    )
    parser.add_argument(
        "--manifest",
        default=str(
            settings.project_root
            / "backend"
            / "app"
            / "evidence"
            / "eures_lmi_2025.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=str(
            settings.project_root
            / "exports"
            / "eures_manifest_candidate.json"
        ),
    )
    args = parser.parse_args()

    result = build_eures_manifest_candidate_from_files(
        args.review,
        args.manifest,
    )

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            result["candidate_manifest"],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    comparison = result["comparison"]
    print("AUGUR EURES MANIFEST CANDIDATE")
    print("=" * 72)
    print(f"output: {output}")
    print(
        "coverage: "
        f"current={comparison['current_unit_group_count']} "
        f"candidate={comparison['candidate_unit_group_count']}"
    )
    print(
        "delta: "
        f"added={len(comparison['added_unit_groups'])} "
        f"removed={len(comparison['removed_unit_groups'])} "
        f"changed_existing={len(comparison['changed_existing_unit_groups'])} "
        f"unchanged_existing={comparison['unchanged_existing_count']}"
    )
    if comparison["removed_unit_groups"]:
        print(
            "removed_unit_groups: "
            + ", ".join(comparison["removed_unit_groups"])
        )
    if comparison["changed_existing_unit_groups"]:
        print(
            "changed_existing_unit_groups: "
            + ", ".join(comparison["changed_existing_unit_groups"])
        )

    print()
    print(
        "NOTE: production evidence was not modified. "
        "The candidate requires explicit human review/promotion."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
