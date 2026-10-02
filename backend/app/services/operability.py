from __future__ import annotations

from app.db.analytics import analytical_evidence_status
from app.esco_store import esco_status
from app.providers import providers_for_country
from app.services.ttv import TEMPORAL_MODEL_VERSION


def operability_status() -> dict:
    evidence = analytical_evidence_status()
    esco = esco_status()
    countries = evidence["countries"]

    provider_coverage = {}
    for country in countries:
        iso3 = country["country_iso3"]
        expected = sorted(
            provider.provider_id
            for provider in providers_for_country(iso3)
        )
        available = sorted(country.get("source_ids") or [])
        missing = sorted(set(expected) - set(available))
        provider_coverage[iso3] = {
            "expected": expected,
            "available": available,
            "missing": missing,
            "complete": len(missing) == 0,
        }

    country_analysis_ready = bool(countries) and all(
        country["observed_rows"] > 0
        and country["observed_indicators"] > 0
        and country["official_forecast_rows"] > 0
        and provider_coverage[country["country_iso3"]]["complete"]
        for country in countries
    )

    local_employment_evidence_ready = bool(countries) and all(
        country["labour_earnings"]["row_count"] > 0
        and country["labour_earnings"]["isco_group_count"] > 0
        for country in countries
    )

    esco_full_ready = (
        esco["mode"] == "full"
        and esco["occupation_count"] > 0
        and esco["skill_count"] > 0
        and esco["relation_count"] > 0
    )

    personal_fit_full_evidence_ready = (
        local_employment_evidence_ready
        and esco_full_ready
    )

    any_country_evidence = any(
        country["observed_rows"] > 0
        or country["official_forecast_rows"] > 0
        or country["labour_earnings"]["row_count"] > 0
        for country in countries
    )

    analysis_ready = (
        country_analysis_ready
        and personal_fit_full_evidence_ready
    )
    ttv_temporal_model_ready = TEMPORAL_MODEL_VERSION is not None
    ready = analysis_ready and ttv_temporal_model_ready

    if ready:
        status = "ready"
    elif any_country_evidence or esco["mode"] != "none":
        status = "partial"
    else:
        status = "empty"

    blockers = []
    if not country_analysis_ready:
        blockers.append("country_analysis_evidence")
    if not local_employment_evidence_ready:
        blockers.append("local_employment_earnings")
    if not esco_full_ready:
        blockers.append("full_esco_dataset")
    if analysis_ready and not ttv_temporal_model_ready:
        blockers.append("ttv_temporal_model")

    return {
        "status": status,
        "ready": ready,
        "analysis_ready": analysis_ready,
        "ttv_temporal_model_ready": ttv_temporal_model_ready,
        "ttv_temporal_model_version": TEMPORAL_MODEL_VERSION,
        "country_analysis_ready": country_analysis_ready,
        "local_employment_evidence_ready": local_employment_evidence_ready,
        "esco_full_ready": esco_full_ready,
        "personal_fit_full_evidence_ready": personal_fit_full_evidence_ready,
        "provider_coverage": provider_coverage,
        "blockers": blockers,
        "evidence": evidence,
        "esco": esco,
        "notes": [
            "Runtime health and analytical operability are separate.",
            "Country analysis requires observed evidence, official forecasts and every configured provider for each registered country.",
            "Full local-employment Personal Fit requires Eurostat labour earnings evidence and a full ESCO dataset.",
            "Full AUGUR readiness also requires a validated TTV temporal model.",
            "Analysis readiness is reported separately from full product readiness.",
            "Partial operability is reported explicitly rather than treating an initialized but incomplete datastore as ready.",
        ],
    }
