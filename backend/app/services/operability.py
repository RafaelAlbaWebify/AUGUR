from __future__ import annotations

from datetime import datetime, timezone

from app.db.analytics import (
    analytical_evidence_status,
    labour_occupation_outlook_status,
    labour_shortage_index_status,
    labour_oja_imbalance_eu27_status,
    subnational_evidence_status,
    subnational_evidence_by_level_status,
    regional_sector_employment_status,
    environmental_health_burden_status,
)
from app.esco_store import esco_status
from app.providers import providers_for_country
from app.services.career_fit import career_market_evidence_status
from app.services.live_postings import live_postings_provider_status
from app.services.ttv import TEMPORAL_MODEL_VERSION
from app.services.ttv_calibration import calibration_status
from app.services.ttv_temporal import temporal_model_validation_status


SYNC_FRESHNESS_MAX_DAYS = 30


def _as_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _age_days(value, now: datetime) -> float | None:
    timestamp = _as_utc(value)
    if timestamp is None:
        return None
    return max(0.0, (now - timestamp).total_seconds() / 86400.0)


def _is_fresh(value, now: datetime) -> bool:
    age_days = _age_days(value, now)
    return (
        age_days is not None
        and age_days <= SYNC_FRESHNESS_MAX_DAYS
    )


def operability_status() -> dict:
    now = datetime.now(timezone.utc)
    evidence = analytical_evidence_status()
    esco = esco_status()
    temporal_validation = temporal_model_validation_status()
    calibration = calibration_status()
    career_market = career_market_evidence_status()
    live_postings = live_postings_provider_status()
    occupation_outlook = labour_occupation_outlook_status()
    future_shortage_index = labour_shortage_index_status()
    oja_imbalance = labour_oja_imbalance_eu27_status()
    subnational = subnational_evidence_status()
    subnational_levels = subnational_evidence_by_level_status()
    for level_status in subnational_levels.values():
        age_days = _age_days(
            level_status.get("latest_retrieved_at"),
            now,
        )
        level_status["age_days"] = (
            round(age_days, 2)
            if age_days is not None
            else None
        )
        level_status["fresh"] = (
            bool(level_status.get("available"))
            and age_days is not None
            and age_days <= SYNC_FRESHNESS_MAX_DAYS
        )
    regional_sector = regional_sector_employment_status()
    environmental_health = environmental_health_burden_status()
    environmental_health_age_days = _age_days(
        environmental_health.get("latest_retrieved_at"),
        now,
    )
    environmental_health["age_days"] = (
        round(environmental_health_age_days, 2)
        if environmental_health_age_days is not None
        else None
    )
    environmental_health["fresh"] = (
        bool(environmental_health.get("available"))
        and environmental_health_age_days is not None
        and environmental_health_age_days <= SYNC_FRESHNESS_MAX_DAYS
    )
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
        retrieved_at = country.get("provider_retrieved_at") or {}

        provider_freshness = {}
        stale = []
        for provider_id in expected:
            age_days = _age_days(retrieved_at.get(provider_id), now)
            fresh = (
                age_days is not None
                and age_days <= SYNC_FRESHNESS_MAX_DAYS
            )
            provider_freshness[provider_id] = {
                "retrieved_at": retrieved_at.get(provider_id),
                "age_days": round(age_days, 2) if age_days is not None else None,
                "fresh": fresh,
            }
            if provider_id in available and not fresh:
                stale.append(provider_id)

        provider_coverage[iso3] = {
            "expected": expected,
            "available": available,
            "missing": missing,
            "stale": stale,
            "freshness_max_days": SYNC_FRESHNESS_MAX_DAYS,
            "providers": provider_freshness,
            "complete": len(missing) == 0,
            "fresh": len(missing) == 0 and len(stale) == 0,
        }

    country_analysis_ready = bool(countries) and all(
        country["observed_rows"] > 0
        and country["observed_indicators"] > 0
        and country["official_forecast_rows"] > 0
        and provider_coverage[country["country_iso3"]]["complete"]
        and provider_coverage[country["country_iso3"]]["fresh"]
        for country in countries
    )

    data_sync_fresh = bool(countries) and all(
        provider_coverage[country["country_iso3"]]["fresh"]
        for country in countries
    )

    local_employment_evidence_ready = bool(countries) and all(
        country["labour_earnings"]["row_count"] > 0
        and country["labour_earnings"]["isco_group_count"] > 0
        and _is_fresh(
            country["labour_earnings"].get("latest_retrieved_at"),
            now,
        )
        and country.get("net_earnings", {}).get("row_count", 0) > 0
        and _is_fresh(
            country.get("net_earnings", {}).get("latest_retrieved_at"),
            now,
        )
        for country in countries
    )

    job_transition_evidence_ready = bool(countries) and all(
        country.get("job_transitions", {}).get("row_count", 0) > 0
        and _is_fresh(
            country.get("job_transitions", {}).get("latest_retrieved_at"),
            now,
        )
        for country in countries
    )

    esco_full_ready = (
        esco["mode"] == "full"
        and esco["occupation_count"] > 0
        and esco["skill_count"] > 0
        and esco["relation_count"] > 0
    )

    personal_fit_core_evidence_ready = (
        local_employment_evidence_ready
        and esco_full_ready
    )
    personal_fit_full_evidence_ready = (
        personal_fit_core_evidence_ready
        and career_market["full_occupation_coverage"]
    )

    any_country_evidence = any(
        country["observed_rows"] > 0
        or country["official_forecast_rows"] > 0
        or country["labour_earnings"]["row_count"] > 0
        for country in countries
    )

    analysis_ready = (
        country_analysis_ready
        and personal_fit_core_evidence_ready
    )
    ttv_temporal_model_ready = (
        TEMPORAL_MODEL_VERSION is not None
        and temporal_validation["ready_for_versioning"]
    )
    ready = (
        analysis_ready
        and ttv_temporal_model_ready
        and job_transition_evidence_ready
    )

    if ready:
        status = "ready"
    elif any_country_evidence or esco["mode"] != "none":
        status = "partial"
    else:
        status = "empty"

    blockers = []
    if not country_analysis_ready:
        blockers.append("country_analysis_evidence")
    if not data_sync_fresh:
        blockers.append("data_sync_stale")
    if not local_employment_evidence_ready:
        blockers.append("local_employment_earnings")
    if not esco_full_ready:
        blockers.append("full_esco_dataset")
    if not job_transition_evidence_ready:
        blockers.append("labour_job_transition_evidence")
    if analysis_ready and not ttv_temporal_model_ready:
        blockers.append("ttv_temporal_model")

    return {
        "status": status,
        "ready": ready,
        "analysis_ready": analysis_ready,
        "ttv_temporal_model_ready": ttv_temporal_model_ready,
        "ttv_temporal_model_version": TEMPORAL_MODEL_VERSION,
        "ttv_temporal_validation": temporal_validation,
        "ttv_calibration": calibration,
        "country_analysis_ready": country_analysis_ready,
        "data_sync_fresh": data_sync_fresh,
        "sync_freshness_max_days": SYNC_FRESHNESS_MAX_DAYS,
        "auxiliary_evidence_freshness_max_days": SYNC_FRESHNESS_MAX_DAYS,
        "local_employment_evidence_ready": local_employment_evidence_ready,
        "job_transition_evidence_ready": job_transition_evidence_ready,
        "esco_full_ready": esco_full_ready,
        "personal_fit_core_evidence_ready": personal_fit_core_evidence_ready,
        "personal_fit_full_evidence_ready": personal_fit_full_evidence_ready,
        "career_market_evidence": career_market,
        "live_postings_provider": live_postings,
        "occupation_outlook_evidence": occupation_outlook,
        "future_shortage_index_evidence": future_shortage_index,
        "eu27_oja_imbalance_evidence": oja_imbalance,
        "subnational_evidence": subnational,
        "subnational_evidence_by_level": subnational_levels,
        "regional_sector_evidence": regional_sector,
        "environmental_health_evidence": environmental_health,
        "provider_coverage": provider_coverage,
        "blockers": blockers,
        "evidence": evidence,
        "esco": esco,
        "notes": [
            "Runtime health and analytical operability are separate.",
            "Country analysis requires observed evidence, official forecasts and every configured provider for each registered country.",
            "Provider synchronization and auxiliary labour evidence retrieval must be no more than 30 days old; source observation years are evaluated separately from retrieval freshness.",
            "Core local-employment Personal Fit requires Eurostat occupational gross earnings, national net-earnings benchmark evidence and a full ESCO dataset.",
            "Full AUGUR readiness also requires loaded job-transition evidence and a validated TTV temporal model.",
            "Analysis readiness uses core Personal Fit evidence and is reported separately from exhaustive market-evidence coverage and full product readiness.",
            "Cedefop STAS occupation outlook is auxiliary forward-looking labour evidence and does not by itself change TTV or full-product readiness.",
            "Cedefop OJA imbalance is exploratory EU27-level occupation context and does not count as country-specific coverage or TTV evidence.",
            "Cedefop CLSSI is forward-looking ISCO-2 shortage context to 2035 and does not count as EURES market-gate or TTV evidence.",
            "Live-postings provider status is informational and does not block public-data operability until a provider is explicitly configured.",
            "NUTS2 labour evidence is regional context and does not imply occupation-specific regional demand unless the source explicitly supports it.",
            "NUTS2 sector-employment evidence describes regional economic structure, not vacancies or hiring probability.",
            "Subnational operability reports NUTS2, NUTS3 and city evidence separately; absence at one level is not silently inferred from another.",
            "Subnational freshness is reported per geographic level and remains informational for national-analysis readiness.",
            "EEA PM2.5 attributable health-burden freshness is reported separately and remains optional for national-analysis readiness.",
            "TTV calibration metrics are descriptive until an external calibration protocol and acceptance criteria are approved.",
            "Partial operability is reported explicitly rather than treating an initialized but incomplete datastore as ready.",
        ],
    }
