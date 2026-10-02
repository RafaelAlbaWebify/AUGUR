from __future__ import annotations

from app.db.bootstrap import initialize_datastores
from app.services.operability import operability_status


def main() -> int:
    initialize_datastores()
    result = operability_status()

    print("AUGUR OPERABILITY")
    print("=" * 72)
    print(f"status: {result['status']}")
    print(f"ready: {result['ready']}")
    print(f"country_analysis_ready: {result['country_analysis_ready']}")
    print(
        "local_employment_evidence_ready: "
        f"{result['local_employment_evidence_ready']}"
    )
    print(f"esco_full_ready: {result['esco_full_ready']}")
    print(
        "personal_fit_full_evidence_ready: "
        f"{result['personal_fit_full_evidence_ready']}"
    )

    if result["blockers"]:
        print("blockers:")
        for blocker in result["blockers"]:
            print(f"  - {blocker}")

    print()
    print("COUNTRY EVIDENCE")
    for country in result["evidence"]["countries"]:
        earnings = country["labour_earnings"]
        print(
            f"{country['country_iso3']}: "
            f"observed={country['observed_indicators']} indicators / "
            f"{country['observed_rows']} rows, "
            f"forecasts={country['official_forecast_rows']}, "
            f"earnings={earnings['isco_group_count']} ISCO groups / "
            f"{earnings['row_count']} rows"
        )

    esco = result["esco"]
    print()
    print(
        "ESCO: "
        f"mode={esco['mode']} "
        f"version={esco['version']} "
        f"occupations={esco['occupation_count']} "
        f"skills={esco['skill_count']} "
        f"relations={esco['relation_count']}"
    )

    if result["status"] == "ready":
        return 0
    if result["status"] == "partial":
        return 2
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
