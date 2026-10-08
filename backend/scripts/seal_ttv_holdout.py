from __future__ import annotations

from app.db.bootstrap import initialize_datastores
from app.services.ttv_calibration import (
    calibration_status,
    seal_holdout,
)


def main() -> int:
    initialize_datastores()
    seal = seal_holdout()
    status = calibration_status()

    print("AUGUR TTV HOLDOUT SEAL")
    print("=" * 72)
    print(f"protocol_version: {seal['protocol_version']}")
    print(
        "acceptance_criteria_version: "
        f"{seal['acceptance_criteria_version']}"
    )
    print(f"case_count: {seal['case_count']}")
    print(f"country_count: {seal['country_count']}")
    print(f"holdout_sha256: {seal['holdout_sha256']}")
    print(f"sealed_at: {seal['sealed_at']}")
    print(
        "acceptance_status: "
        f"{status['holdout_acceptance']['status']}"
    )
    print(
        "NOTE: sealing prevents additional holdout cases for this protocol. "
        "Representativeness review is still required before model activation."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
