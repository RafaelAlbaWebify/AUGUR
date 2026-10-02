from __future__ import annotations

import argparse

from app.db.bootstrap import initialize_datastores
from app.services.ttv_calibration import (
    calibration_status,
    import_calibration_csv,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Import anonymous observed TTV calibration cases "
            "into the local AUGUR SQLite store."
        )
    )
    parser.add_argument(
        "path",
        help="CSV file containing observed calibration cases.",
    )
    args = parser.parse_args()

    initialize_datastores()

    result = import_calibration_csv(args.path)
    status = calibration_status()

    print("AUGUR TTV CALIBRATION IMPORT")
    print("=" * 72)
    print(f"schema_version: {result['schema_version']}")
    print(f"imported_count: {result['imported_count']}")
    print(f"case_count: {status['case_count']}")
    print(f"country_count: {status['country_count']}")
    print(
        "interval_coverage_pct: "
        f"{status['interval_coverage_pct']}"
    )
    print(
        "mean_absolute_midpoint_error_weeks: "
        f"{status['mean_absolute_midpoint_error_weeks']}"
    )
    print(
        "mean_signed_midpoint_error_weeks: "
        f"{status['mean_signed_midpoint_error_weeks']}"
    )
    print("externally_calibrated: False")
    print(
        "NOTE: importing observations does not activate "
        "the external-calibration gate."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
