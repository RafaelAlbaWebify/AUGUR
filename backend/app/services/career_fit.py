from __future__ import annotations

import json
from pathlib import Path

from app.db.analytics import (
    latest_labour_job_vacancy_rate,
    latest_labour_occupation_outlook,
    latest_labour_oja_imbalance_eu27,
)
from app.models.profile import PersonalProfileResponse
from app.services.esco_match import match_profile_skills
from app.services.live_postings import provider_not_configured_evidence
from app.esco_store import search_occupations


EURES_EVIDENCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "eures_lmi_2025.json"
)


def _load_eures_evidence() -> tuple[dict, dict]:
    payload = json.loads(EURES_EVIDENCE_PATH.read_text(encoding="utf-8"))
    countries = {
        country_iso3: {
            **config,
            "shortage_groups": set(config["shortage_groups"]),
            "surplus_groups": set(config["surplus_groups"]),
        }
        for country_iso3, config in payload["countries"].items()
    }
    metadata = {
        key: value
        for key, value in payload.items()
        if key != "countries"
    }
    return metadata, countries


EURES_EVIDENCE_METADATA, COUNTRY_EVIDENCE = _load_eures_evidence()
BROAD_EVIDENCE_METADATA = EURES_EVIDENCE_METADATA["broad_evidence"]
UNIT_GROUP_EVIDENCE_METADATA = EURES_EVIDENCE_METADATA["unit_group_evidence"]
RULE_VERSION = EURES_EVIDENCE_METADATA["rule_version"]


ISCO_SUBMAJOR_TO_MARKET_GROUP = {
    "21": "science_engineering_professionals",
    "22": "health_professionals",
    "25": "ict_professionals",
    "26": "legal_social_cultural_professionals",
    "31": "science_engineering_associate_professionals",
    "33": "business_administration_associate_professionals",
    "35": "information_communications_technicians",
    "52": "sales_workers",
    "72": "metal_machinery_trades_workers",
    "81": "plant_machine_operators",
    "92": "agricultural_forestry_fishery_labourers",
}


ESCO_OCCUPATION_MATCH_THRESHOLD = 0.72

EXPERIMENTAL_VACANCY_DATASET_ID = "jvs_a_isco3_r1"
EXPERIMENTAL_VACANCY_SUPPORTED_COUNTRIES = {"ESP", "PRT"}


def career_market_evidence_status() -> dict:
    unit_groups = EURES_EVIDENCE_METADATA.get("unit_group_signals", {})
    supported_countries = sorted(COUNTRY_EVIDENCE)
    broad_country_count = sum(
        1
        for country in COUNTRY_EVIDENCE.values()
        if country.get("shortage_groups") is not None
        and country.get("surplus_groups") is not None
    )

    return {
        "evidence_id": EURES_EVIDENCE_METADATA["evidence_id"],
        "rule_version": EURES_EVIDENCE_METADATA["rule_version"],
        "broad_evidence": BROAD_EVIDENCE_METADATA,
        "unit_group_evidence": UNIT_GROUP_EVIDENCE_METADATA,
        "report_year": UNIT_GROUP_EVIDENCE_METADATA["report_year"],
        "conditions_year": UNIT_GROUP_EVIDENCE_METADATA["conditions_year"],
        "supported_countries": supported_countries,
        "broad_country_count": broad_country_count,
        "unit_group_count": len(unit_groups),
        "coverage_scope": (
            "partial_unit_group_coverage"
            if unit_groups
            else "broad_groups_only"
        ),
        "full_occupation_coverage": False,
        "notes": [
            "Broad country-level occupation groups are implemented for all supported countries.",
            "Verified ISCO unit-group evidence currently covers only selected occupations.",
            "CareerFit exposes incomplete market coverage instead of treating the EURES catalog as exhaustive.",
        ],
    }


def resolve_esco_occupation(profession: str | None) -> dict:
    if not profession or not profession.strip():
        return {
            "status": "profession_missing",
            "selected": None,
            "candidates": [],
            "threshold": ESCO_OCCUPATION_MATCH_THRESHOLD,
        }

    candidates = search_occupations(profession, limit=5)
    selected = (
        candidates[0]
        if candidates and candidates[0]["match_score"] >= ESCO_OCCUPATION_MATCH_THRESHOLD
        else None
    )

    return {
        "status": "matched" if selected else "no_confident_match",
        "selected": selected,
        "candidates": candidates,
        "threshold": ESCO_OCCUPATION_MATCH_THRESHOLD,
    }

def classify_esco_market_group(
    occupation_match: dict,
) -> dict | None:
    selected = occupation_match.get("selected")
    if not selected:
        return None

    raw_isco = str(selected.get("isco_group") or selected.get("code") or "")
    digits = "".join(character for character in raw_isco if character.isdigit())
    if len(digits) < 2:
        return None

    submajor = digits[:2]
    group = ISCO_SUBMAJOR_TO_MARKET_GROUP.get(submajor)
    if group is None:
        return {
            "status": "isco_group_unmapped",
            "occupation_group": f"isco_{submajor}",
            "matched_terms": [],
            "mapping_method": "esco_isco_submajor",
            "isco_submajor": submajor,
        }

    return {
        "status": "mapped",
        "occupation_group": group,
        "matched_terms": [],
        "mapping_method": "esco_isco_submajor",
        "isco_submajor": submajor,
    }


OCCUPATION_RULES = [
    (
        "ict_professionals",
        [
            "software",
            "developer",
            "programmer",
            "systems analyst",
            "system analyst",
            "cybersecurity",
            "cyber security",
            "network engineer",
            "cloud engineer",
            "systems engineer",
            "system engineer",
            "it support",
            "support engineer",
            "system administrator",
            "systems administrator",
            "devops",
            "data engineer",
            "database administrator",
            "it engineer",
            "information technology",
            "ict",
        ],
    ),
    (
        "science_engineering_professionals",
        [
            "engineer",
            "engineering",
            "scientist",
            "architect",
        ],
    ),
    (
        "health_professionals",
        [
            "doctor",
            "physician",
            "nurse",
            "pharmacist",
            "dentist",
            "physiotherapist",
            "health professional",
        ],
    ),
    (
        "business_administration_associate_professionals",
        [
            "administrative",
            "administrator",
            "business support",
            "office manager",
            "bookkeeper",
        ],
    ),
    (
        "legal_social_cultural_professionals",
        [
            "lawyer",
            "solicitor",
            "legal",
            "social worker",
            "journalist",
            "translator",
        ],
    ),
    (
        "sales_workers",
        [
            "sales",
            "retail",
            "shop assistant",
            "cashier",
        ],
    ),
    (
        "metal_machinery_trades_workers",
        [
            "welder",
            "machinist",
            "mechanic",
            "metal worker",
            "toolmaker",
        ],
    ),
    (
        "plant_machine_operators",
        [
            "machine operator",
            "plant operator",
            "production operator",
        ],
    ),
    (
        "agricultural_forestry_fishery_labourers",
        [
            "farm worker",
            "agricultural worker",
            "forestry worker",
            "fishery worker",
        ],
    ),
]


def classify_occupation(profession: str | None) -> dict:
    if not profession or not profession.strip():
        return {
            "status": "profession_missing",
            "occupation_group": None,
            "matched_terms": [],
            "mapping_method": "keyword_fallback",
            "isco_submajor": None,
        }

    text = profession.strip().lower()
    matches = []

    for group, keywords in OCCUPATION_RULES:
        matched_terms = [
            keyword
            for keyword in keywords
            if keyword in text
        ]
        if matched_terms:
            matches.append(
                {
                    "occupation_group": group,
                    "matched_terms": matched_terms,
                }
            )

    if not matches:
        return {
            "status": "occupation_unmapped",
            "occupation_group": None,
            "matched_terms": [],
            "mapping_method": "keyword_fallback",
            "isco_submajor": None,
        }

    # Prefer the most specific match by longest matched keyword.
    matches.sort(
        key=lambda item: max(len(term) for term in item["matched_terms"]),
        reverse=True,
    )
    best = matches[0]

    return {
        "status": "mapped",
        "occupation_group": best["occupation_group"],
        "matched_terms": best["matched_terms"],
        "mapping_method": "keyword_fallback",
        "isco_submajor": None,
    }


def unit_group_market_signal(
    target_country_iso3: str,
    occupation_match: dict,
) -> dict | None:
    selected = occupation_match.get("selected")
    if not selected:
        return None

    raw_isco = str(selected.get("isco_group") or selected.get("code") or "")
    digits = "".join(character for character in raw_isco if character.isdigit())
    if len(digits) < 4:
        return None

    isco_unit = digits[:4]
    config = EURES_EVIDENCE_METADATA.get("unit_group_signals", {}).get(isco_unit)
    if config is None:
        return None

    target = target_country_iso3.upper()
    country_evidence = COUNTRY_EVIDENCE.get(target)
    eures_country_code = (
        country_evidence.get("eures_country_code")
        if country_evidence
        else None
    )
    if eures_country_code is None:
        return None

    in_shortage = eures_country_code in config["shortage_countries"]
    in_surplus = eures_country_code in config["surplus_countries"]

    if in_shortage and in_surplus:
        signal = "mixed_shortage_and_surplus"
    elif in_shortage:
        signal = "shortage"
    elif in_surplus:
        signal = "surplus"
    else:
        signal = "not_classified_as_shortage_or_surplus"

    return {
        "signal": signal,
        "isco_unit": isco_unit,
        "occupation_label": config["occupation_label"],
        "scope": "isco_unit_group",
    }


def market_signal_source(
    country_evidence: dict,
    unit_signal: dict | None,
) -> dict:
    if unit_signal is not None:
        return {
            "label": "EURES Report on labour shortages and surpluses 2025 — Annex",
            "url": UNIT_GROUP_EVIDENCE_METADATA["publication_url"],
            "evidence_id": UNIT_GROUP_EVIDENCE_METADATA["evidence_id"],
            "rule_version": UNIT_GROUP_EVIDENCE_METADATA["rule_version"],
            "report_year": UNIT_GROUP_EVIDENCE_METADATA["report_year"],
            "conditions_year": UNIT_GROUP_EVIDENCE_METADATA["conditions_year"],
            "report_url": UNIT_GROUP_EVIDENCE_METADATA["report_url"],
            "scope": "isco_unit_group",
        }

    return {
        "label": country_evidence["source_label"],
        "url": country_evidence["source_url"],
        "evidence_id": BROAD_EVIDENCE_METADATA["evidence_id"],
        "rule_version": BROAD_EVIDENCE_METADATA["rule_version"],
        "report_year": BROAD_EVIDENCE_METADATA["report_year"],
        "conditions_year": BROAD_EVIDENCE_METADATA["conditions_year"],
        "report_url": country_evidence["source_url"],
        "scope": "broad_occupation_group",
    }


def occupation_vacancy_demand_evidence(
    target_country_iso3: str,
    occupation_match: dict,
) -> dict | None:
    selected = occupation_match.get("selected")
    if not selected:
        return None

    raw_isco = str(selected.get("isco_group") or selected.get("code") or "")
    digits = "".join(character for character in raw_isco if character.isdigit())
    if not digits:
        return None

    isco_major = f"OC{digits[0]}"
    isco_3digit = f"OC{digits[:3]}" if len(digits) >= 3 else None
    target = target_country_iso3.upper()

    if target not in EXPERIMENTAL_VACANCY_SUPPORTED_COUNTRIES:
        return {
            "status": "source_coverage_unavailable",
            "dataset_id": EXPERIMENTAL_VACANCY_DATASET_ID,
            "supported_countries": sorted(EXPERIMENTAL_VACANCY_SUPPORTED_COUNTRIES),
            "isco_major": isco_major,
            "isco_3digit": isco_3digit,
            "granularity": "isco_3digit",
            "role": "context_only",
            "notes": [
                "Eurostat experimental ISCO-3 vacancy evidence does not cover this target country.",
                "Unavailable source coverage must not be interpreted as zero vacancy demand.",
            ],
        }

    row = (
        latest_labour_job_vacancy_rate(
            target_country_iso3,
            isco_3digit,
        )
        if isco_3digit
        else None
    )
    granularity = "isco_3digit"

    if row is None:
        row = latest_labour_job_vacancy_rate(
            target_country_iso3,
            isco_major,
        )
        granularity = "isco_major_group"

    if row is None:
        return {
            "status": "evidence_missing",
            "isco_major": isco_major,
            "isco_3digit": isco_3digit,
            "granularity": (
                "isco_3digit"
                if isco_3digit
                else "isco_major_group"
            ),
            "role": "context_only",
        }

    return {
        "status": "available",
        "isco_major": isco_major,
        "isco_3digit": isco_3digit,
        "vacancy_rate_pct": row["vacancy_rate_pct"],
        "period": row["period"],
        "nace_scope": row.get("nace_scope"),
        "source_id": row["source_id"],
        "dataset_id": row["dataset_id"],
        "source_updated_at": row.get("source_updated_at"),
        "granularity": granularity,
        "role": "context_only",
        "notes": [
            "Vacancy rate is unmet-demand context, not a job-finding probability.",
            "ISCO 3-digit vacancy evidence is preferred when Eurostat publishes it for the target country.",
            "Experimental occupation vacancy evidence uses online job advertisements and can be biased toward occupations more often advertised online.",
            "This evidence does not change CareerFit completeness or TTV timing.",
        ],
    }






def eu27_oja_imbalance_evidence(
    occupation_match: dict,
) -> dict | None:
    selected = occupation_match.get("selected")
    if not selected:
        return None

    raw_isco = str(selected.get("isco_group") or selected.get("code") or "")
    digits = "".join(character for character in raw_isco if character.isdigit())
    if len(digits) < 4:
        return None

    isco_unit = digits[:4]
    row = latest_labour_oja_imbalance_eu27(isco_unit)
    if row is None:
        return {
            "status": "evidence_missing",
            "isco08": isco_unit,
            "geographic_scope": "EU27",
            "dataset_id": "CEDEFOP_OJA_IMBALANCE",
            "role": "context_only",
        }

    return {
        "status": "available",
        "isco08": row["isco08"],
        "occupation_label": row["occupation_label"],
        "score": row["score"],
        "source_id": row["source_id"],
        "dataset_id": row["dataset_id"],
        "release_version": row["release_version"],
        "geographic_scope": "EU27",
        "role": "context_only",
        "notes": [
            "The published score is a single EU27-level exploratory recruitment-pressure signal.",
            "Higher values indicate stronger signals of potential occupational shortage in online job advertisements.",
            "The score is not country-specific and is not a hiring probability.",
            "This evidence does not change CareerFit completeness, market gates or TTV timing.",
        ],
    }

def occupation_outlook_evidence(
    target_country_iso3: str,
    occupation_match: dict,
) -> dict | None:
    selected = occupation_match.get("selected")
    if not selected:
        return None

    raw_isco = str(selected.get("isco_group") or selected.get("code") or "")
    digits = "".join(character for character in raw_isco if character.isdigit())
    if not digits:
        return None

    candidates = []
    if len(digits) >= 2:
        candidates.append((digits[:2], "isco_2digit"))
    candidates.append((digits[:1], "isco_1digit"))

    for isco_code, granularity in candidates:
        rows = latest_labour_occupation_outlook(
            target_country_iso3,
            isco_code,
        )
        if not rows:
            continue

        return {
            "status": "available",
            "source_id": rows[0]["source_id"],
            "dataset_id": rows[0]["dataset_id"],
            "release_version": rows[0]["release_version"],
            "isco08": isco_code,
            "granularity": granularity,
            "occupation_label": rows[0].get("occupation_label"),
            "scenario": rows[0]["scenario"],
            "horizons": [
                {
                    "period": row["period"],
                    "employment_level_thousands": row.get("employment_level_thousands"),
                    "employment_growth_pct": row.get("employment_growth_pct"),
                }
                for row in rows
            ],
            "role": "context_only",
            "notes": [
                "Cedefop STAS is a short-term occupation outlook, not a job-finding probability.",
                "ISCO 2-digit evidence is preferred; ISCO 1-digit is a fallback.",
                "STAS outlook does not change CareerFit completeness or TTV timing.",
            ],
        }

    return {
        "status": "evidence_missing",
        "dataset_id": "CEDEFOP_STAS",
        "isco_2digit": digits[:2] if len(digits) >= 2 else None,
        "isco_1digit": digits[:1],
        "role": "context_only",
    }

def occupation_outlook_trend_evidence(
    outlook: dict | None,
) -> dict:
    if not outlook or outlook.get("status") != "available":
        return {
            "status": "evidence_missing",
            "evidence_type": "short_term_employment_outlook",
            "role": "context_only",
        }

    horizons = [
        item
        for item in outlook.get("horizons", [])
        if item.get("employment_growth_pct") is not None
    ]
    if not horizons:
        return {
            "status": "evidence_missing",
            "evidence_type": "short_term_employment_outlook",
            "source_id": outlook.get("source_id"),
            "dataset_id": outlook.get("dataset_id"),
            "role": "context_only",
        }

    latest = max(horizons, key=lambda item: item["period"])
    growth = float(latest["employment_growth_pct"])
    if growth > 0:
        direction = "positive_growth"
    elif growth < 0:
        direction = "negative_growth"
    else:
        direction = "zero_growth"

    return {
        "status": "available",
        "evidence_type": "short_term_employment_outlook",
        "source_id": outlook.get("source_id"),
        "dataset_id": outlook.get("dataset_id"),
        "release_version": outlook.get("release_version"),
        "isco08": outlook.get("isco08"),
        "granularity": outlook.get("granularity"),
        "scenario": outlook.get("scenario"),
        "latest_period": latest["period"],
        "latest_growth_pct": growth,
        "direction": direction,
        "horizons": horizons,
        "role": "context_only",
        "notes": [
            "This is Cedefop STAS employment-outlook evidence, not online-job-ad demand growth.",
            "The direction label reflects only the sign of the published growth value; it is not statistical significance.",
            "The signal does not change CareerFit completeness, market gates or TTV timing.",
        ],
    }


def language_oja_requirements_evidence() -> dict:
    return {
        "status": "source_access_gated",
        "source_id": "CEDEFOP",
        "dataset_id": "CEDEFOP_SKILLS_OVATE",
        "requested_metric": "language_demand_share_in_online_job_ads",
        "access_path": "Eurostat Microdata access portal",
        "public_dashboard": "Skills-OVATE",
        "reproducible_public_ingestion": False,
        "role": "withheld_until_reproducible_access",
        "notes": [
            "Skills-OVATE exposes language-related OJA analytics interactively, but detailed data access is organised through Eurostat microdata access.",
            "AUGUR does not scrape Tableau dashboards.",
            "The public 2026 OJA imbalance score includes non-native-language change only as one combined-score component and cannot be decomposed into a country language-demand share.",
        ],
    }


def skill_demand_trend_evidence() -> dict:
    return {
        "status": "source_access_gated",
        "source_id": "CEDEFOP",
        "dataset_id": "CEDEFOP_SKILLS_OVATE",
        "requested_metric": "skill_demand_share_and_time_trend_in_online_job_ads",
        "access_path": "Eurostat Microdata access portal",
        "public_dashboard": "Skills-OVATE",
        "reproducible_public_ingestion": False,
        "role": "withheld_until_reproducible_access",
        "notes": [
            "Detailed Skills-OVATE skill shares and time trends are not ingested from a stable public API or download.",
            "ESCO skill relationships are taxonomy evidence and are not substituted for employer-demand frequency.",
            "The EU27 OJA imbalance score is a combined occupation-level signal and is not a published skill time series.",
        ],
    }


def career_fit(
    profile: PersonalProfileResponse,
    target_country_iso3: str,
) -> dict:
    target = target_country_iso3.upper()
    evidence = COUNTRY_EVIDENCE.get(target)
    occupation_match = resolve_esco_occupation(profile.profession)
    classification = (
        classify_esco_market_group(occupation_match)
        or classify_occupation(profile.profession)
    )
    esco_label = occupation_match["selected"]["preferred_label"] if occupation_match["selected"] else None
    vacancy_demand_evidence = occupation_vacancy_demand_evidence(
        target,
        occupation_match,
    )
    occupation_outlook = occupation_outlook_evidence(
        target,
        occupation_match,
    )
    occupation_trend = occupation_outlook_trend_evidence(
        occupation_outlook,
    )
    language_oja_requirements = language_oja_requirements_evidence()
    skill_demand_trend = skill_demand_trend_evidence()
    eu27_oja_imbalance = eu27_oja_imbalance_evidence(
        occupation_match,
    )
    live_postings_evidence = provider_not_configured_evidence()

    if evidence is None:
        return {
            "target_country_iso3": target,
            "status": "country_evidence_missing",
            "occupation": classification,
            "market_signal": None,
            "rule_version": RULE_VERSION,
            "source": None,
            "occupation_match": occupation_match,
            "vacancy_demand_evidence": vacancy_demand_evidence,
            "occupation_outlook_evidence": occupation_outlook,
            "occupation_trend_evidence": occupation_trend,
            "skill_demand_trend_evidence": skill_demand_trend,
            "language_oja_requirements_evidence": language_oja_requirements,
            "eu27_oja_imbalance_evidence": eu27_oja_imbalance,
            "live_postings_evidence": live_postings_evidence,
            "skill_match": {
                "status": "not_evaluated",
                "matched_skills": [],
                "missing_skills": [],
            },
            "evidence_complete": False,
            "profile_skill_coverage_complete": False,
            "market_signal_supports_viability": False,
            "viability_evidence_ready": False,
            "notes": [
                "No verified EURES country evidence is implemented for this target.",
                "No demand signal is inferred.",
            ],
        }

    group = classification["occupation_group"]

    if group is None:
        return {
            "target_country_iso3": target,
            "status": classification["status"],
            "occupation": classification,
            "market_signal": None,
            "rule_version": BROAD_EVIDENCE_METADATA["rule_version"],
            "source": market_signal_source(evidence, None),
            "occupation_match": occupation_match,
            "vacancy_demand_evidence": vacancy_demand_evidence,
            "occupation_outlook_evidence": occupation_outlook,
            "occupation_trend_evidence": occupation_trend,
            "skill_demand_trend_evidence": skill_demand_trend,
            "language_oja_requirements_evidence": language_oja_requirements,
            "eu27_oja_imbalance_evidence": eu27_oja_imbalance,
            "live_postings_evidence": live_postings_evidence,
            "skill_match": {
                "status": "not_evaluated",
                "matched_skills": [],
                "missing_skills": [],
            },
            "evidence_complete": False,
            "profile_skill_coverage_complete": False,
            "market_signal_supports_viability": False,
            "viability_evidence_ready": False,
            "notes": [
                "CareerFit requires a mapped occupation group before EURES shortage/surplus evidence can be applied.",
                "No country-fit score is produced.",
            ],
        }

    unit_signal = unit_group_market_signal(target, occupation_match)

    if unit_signal is not None:
        market_signal = unit_signal["signal"]
        market_signal_scope = unit_signal["scope"]
        market_signal_isco = unit_signal["isco_unit"]
    elif group in evidence["shortage_groups"]:
        market_signal = "shortage"
        market_signal_scope = "broad_occupation_group"
        market_signal_isco = classification.get("isco_submajor")
    elif group in evidence["surplus_groups"]:
        market_signal = "surplus"
        market_signal_scope = "broad_occupation_group"
        market_signal_isco = classification.get("isco_submajor")
    else:
        market_signal = "not_classified_as_shortage_or_surplus"
        market_signal_scope = "broad_occupation_group"
        market_signal_isco = classification.get("isco_submajor")

    market_source = market_signal_source(evidence, unit_signal)

    skill_match = (
        match_profile_skills(esco_label, profile.skills)
        if esco_label
        else {
            "status": "occupation_not_mapped_to_esco",
            "dataset_mode": None,
            "dataset_version": None,
            "occupation_label": None,
            "matched_skills": [],
            "missing_skills": [],
            "coverage": None,
            "evidence_complete": False,
        }
    )

    essential_total = skill_match.get("essential_skill_count") or 0
    essential_matched = skill_match.get("essential_skills_matched") or 0
    skill_coverage = skill_match.get("coverage")

    skill_evidence_complete = bool(
        skill_match.get("evidence_complete")
    )
    market_evidence_complete = unit_signal is not None

    profile_skill_coverage_complete = bool(
        skill_evidence_complete
        and essential_total > 0
        and essential_matched == essential_total
        and skill_coverage == 1.0
    )
    market_signal_supports_viability = bool(
        market_evidence_complete
        and market_signal == "shortage"
    )
    evidence_complete = bool(
        skill_evidence_complete
        and market_evidence_complete
    )
    viability_evidence_ready = bool(
        evidence_complete
        and profile_skill_coverage_complete
        and market_signal_supports_viability
    )

    return {
        "target_country_iso3": target,
        "status": "evidence_available",
        "occupation": classification,
        "market_signal": market_signal,
        "market_signal_scope": market_signal_scope,
        "market_signal_isco": market_signal_isco,
        "rule_version": market_source["rule_version"],
        "source": market_source,
        "occupation_match": occupation_match,
        "vacancy_demand_evidence": vacancy_demand_evidence,
        "occupation_outlook_evidence": occupation_outlook,
        "occupation_trend_evidence": occupation_trend,
        "skill_demand_trend_evidence": skill_demand_trend,
        "language_oja_requirements_evidence": language_oja_requirements,
        "eu27_oja_imbalance_evidence": eu27_oja_imbalance,
        "live_postings_evidence": live_postings_evidence,
        "skill_match": skill_match,
        "skill_evidence_complete": skill_evidence_complete,
        "market_evidence_complete": market_evidence_complete,
        "evidence_complete": evidence_complete,
        "profile_skill_coverage_complete": profile_skill_coverage_complete,
        "market_signal_supports_viability": market_signal_supports_viability,
        "viability_evidence_ready": viability_evidence_ready,
        "notes": [
            "EURES shortage/surplus groups are broad labour-market signals, not guarantees of job availability.",
            f"Market signal source: {market_source['evidence_id']} · {market_source['conditions_year']} conditions · {market_source['scope']}.",
            "Eurostat vacancy-rate evidence is contextual demand evidence at ISCO major-group level and does not change the shortage/surplus gate.",
            "Cedefop STAS provides short-term occupation outlook context and does not change the shortage/surplus gate or TTV timing.",
            "Cedefop OJA imbalance provides an exploratory EU27-level ISCO-4 recruitment-pressure context and does not change country-specific market gates or TTV timing.",
            "Live posting counts, salary, seniority, location and employer-specific skill/language requirements remain unavailable until a live-postings provider is configured.",
            "When ESCO resolves an occupation confidently, CareerFit uses verified EURES ISCO unit-group evidence first, then the ISCO sub-major group; keyword classification is only a fallback.",
            "Verified unit-group evidence takes precedence over broad occupational-group signals when both exist.",
            "Broad-group EURES evidence remains descriptive but does not count as complete CareerFit evidence for TTV.",
            "ISCO 25 ICT professionals and ISCO 35 information and communications technicians are kept distinct.",
            "Essential ESCO skills are treated as conservative profile-evidence requirements; missing declarations are not inferred as present.",
            "A shortage signal plus complete declared essential-skill coverage is an evidence gate, not a guarantee of employment.",
            "No country ranking or composite score is produced.",
        ],
    }
