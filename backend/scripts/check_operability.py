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
    print(f"analysis_ready: {result['analysis_ready']}")
    print(
        "ttv_temporal_model_ready: "
        f"{result['ttv_temporal_model_ready']}"
    )
    print(
        "ttv_temporal_model_version: "
        f"{result['ttv_temporal_model_version']}"
    )
    print(f"country_analysis_ready: {result['country_analysis_ready']}")

    print()
    print("TTV TEMPORAL VALIDATION")
    validation = result["ttv_temporal_validation"]
    print(f"ready_for_versioning: {validation['ready_for_versioning']}")
    for gate_id, gate in validation["gates"].items():
        print(
            f"  {gate_id}: {gate['state']} "
            f"({gate['reason']})"
        )
    print(
        "data_sync_fresh: "
        f"{result['data_sync_fresh']} "
        f"(max {result['sync_freshness_max_days']} days)"
    )
    print(
        "local_employment_evidence_ready: "
        f"{result['local_employment_evidence_ready']}"
    )
    print(
        "job_transition_evidence_ready: "
        f"{result['job_transition_evidence_ready']}"
    )
    print(f"esco_full_ready: {result['esco_full_ready']}")
    print(
        "personal_fit_core_evidence_ready: "
        f"{result['personal_fit_core_evidence_ready']}"
    )
    print(
        "personal_fit_full_evidence_ready: "
        f"{result['personal_fit_full_evidence_ready']}"
    )

    career_market = result["career_market_evidence"]
    print(
        "career_market_evidence: "
        f"scope={career_market['coverage_scope']} "
        f"countries={career_market['broad_country_count']} "
        f"verified_unit_groups={career_market['unit_group_count']} "
        f"full_occupation_coverage={career_market['full_occupation_coverage']}"
    )

    if result["blockers"]:
        print("blockers:")
        for blocker in result["blockers"]:
            print(f"  - {blocker}")

        if (
            "data_sync_stale" in result["blockers"]
            or "local_employment_earnings" in result["blockers"]
            or "labour_job_transition_evidence" in result["blockers"]
        ):
            print()
            print(
                "Refresh hint: run .\\refresh-augur.ps1 "
                "to synchronize official evidence and re-check operability."
            )

    print()
    print("TTV CALIBRATION")
    calibration = result["ttv_calibration"]
    print(
        f"infrastructure_ready: "
        f"{calibration['infrastructure_ready']}"
    )
    print(f"protocol_state: {calibration['protocol_state']}")
    print(f"protocol_version: {calibration['protocol_version']}")
    protocol_readiness = calibration["protocol_readiness"]
    print(
        "ready_for_holdout_collection: "
        f"{protocol_readiness['ready_for_holdout_collection']}"
    )
    if protocol_readiness["blockers"]:
        print("protocol_blockers:")
        for blocker in protocol_readiness["blockers"]:
            print(f"  - {blocker}")
    print(f"case_count: {calibration['case_count']}")
    print(f"country_count: {calibration['country_count']}")
    print(
        "interval_coverage_pct: "
        f"{calibration['interval_coverage_pct']}"
    )
    print(
        "mean_absolute_midpoint_error_weeks: "
        f"{calibration['mean_absolute_midpoint_error_weeks']}"
    )
    print(
        "externally_calibrated: "
        f"{calibration['externally_calibrated']}"
    )
    if calibration.get("sample_role_metrics"):
        print("sample_role_metrics:")
        for role, metrics in calibration["sample_role_metrics"].items():
            print(
                f"  {role}: "
                f"cases={metrics['case_count']} "
                f"coverage={metrics['interval_coverage_pct']}% "
                f"mae={metrics['mean_absolute_midpoint_error_weeks']}w "
                f"bias={metrics['mean_signed_midpoint_error_weeks']}w"
            )

    if calibration.get("stage_metrics"):
        print("stage_metrics:")
        for stage_id, metrics in calibration["stage_metrics"].items():
            print(
                f"  {stage_id}: "
                f"cases={metrics['case_count']} "
                f"coverage={metrics['interval_coverage_pct']}% "
                f"mae={metrics['mean_absolute_midpoint_error_weeks']}w "
                f"bias={metrics['mean_signed_midpoint_error_weeks']}w"
            )

    print()
    print("COUNTRY EVIDENCE")
    for country in result["evidence"]["countries"]:
        earnings = country["labour_earnings"]
        net_earnings = country["net_earnings"]
        job_transitions = country["job_transitions"]
        job_vacancies = country["job_vacancies"]
        print(
            f"{country['country_iso3']}: "
            f"observed={country['observed_indicators']} indicators / "
            f"{country['observed_rows']} rows, "
            f"forecasts={country['official_forecast_rows']}, "
            f"earnings={earnings['isco_group_count']} ISCO groups / "
            f"{earnings['row_count']} rows, "
            f"net_earnings={net_earnings['row_count']} rows "
            f"(latest={net_earnings['latest_period']}), "
            f"job_transitions={job_transitions['age_group_count']} age groups / "
            f"{job_transitions['row_count']} rows, "
            f"job_vacancies={job_vacancies['isco_group_count']} ISCO groups / "
            f"{job_vacancies['row_count']} rows "
            f"(latest={job_vacancies['latest_period']})"
        )

    print()
    print("PROVIDER COVERAGE")
    for country_iso3, coverage in result["provider_coverage"].items():
        missing = ", ".join(coverage["missing"]) if coverage["missing"] else "none"
        stale = ", ".join(coverage.get("stale", [])) if coverage.get("stale") else "none"
        print(
            f"{country_iso3}: complete={coverage['complete']} "
            f"fresh={coverage.get('fresh', False)} "
            f"missing={missing} "
            f"stale={stale}"
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
