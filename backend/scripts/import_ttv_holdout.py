from __future__ import annotations

import argparse

from app.db.bootstrap import initialize_datastores
from app.services.ttv_calibration import (
    calibration_status,
    import_holdout_calibration_csv,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Import a frozen TTV v1 holdout batch into the local AUGUR "
            "calibration store."
        )
    )
    parser.add_argument(
        "path",
        help="CSV file containing holdout calibration cases.",
    )
    args = parser.parse_args()

    initialize_datastores()
    result = import_holdout_calibration_csv(args.path)
    status = calibration_status()

    print("AUGUR TTV HOLDOUT IMPORT")
    print("=" * 72)
    print(f"protocol_version: {result['frozen_protocol_version']}")
    print(
        "acceptance_criteria_version: "
        f"{result['acceptance_criteria_version']}"
    )
    print(f"imported_count: {result['imported_count']}")
    print(f"holdout_case_count: {status['holdout_case_count']}")
    print(
        "holdout_acceptance_status: "
        f"{status['holdout_acceptance']['status']}"
    )
    print(
        "NOTE: importing a holdout does not activate the model. "
        "Representativeness review and acceptance evaluation remain required."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
