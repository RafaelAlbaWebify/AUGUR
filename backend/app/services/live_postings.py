from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


LIVE_POSTINGS_CONTRACT_VERSION = "live-postings-v1"

REQUIRED_ANALYTICS_CAPABILITIES = {
    "active_postings",
    "country_filter",
    "occupation_filter",
    "posting_date",
}

OPTIONAL_ANALYTICS_CAPABILITIES = {
    "region_filter",
    "skills",
    "languages",
    "salary",
    "historical_postings",
    "employer",
}


@dataclass(frozen=True)
class LivePostingsQuery:
    country_iso3: str
    occupation_label: str
    isco08: str | None = None
    region_code: str | None = None
    lookback_days: int = 30
    limit: int = 200


@dataclass(frozen=True)
class LivePostingsCapabilities:
    provider_id: str
    capabilities: frozenset[str]

    @property
    def supports_core_analytics(self) -> bool:
        return REQUIRED_ANALYTICS_CAPABILITIES.issubset(
            self.capabilities
        )


class LivePostingsProvider(Protocol):
    provider_id: str
    capabilities: LivePostingsCapabilities

    def fetch_snapshot(self, query: LivePostingsQuery) -> dict:
        ...


def provider_not_configured_evidence() -> dict:
    return {
        "status": "provider_not_configured",
        "contract_version": LIVE_POSTINGS_CONTRACT_VERSION,
        "provider_id": None,
        "role": "context_only",
        "requested_metrics": [
            "active_posting_count",
            "skill_demand_share",
            "language_requirement_share",
            "salary_context",
            "posting_trend",
        ],
        "required_capabilities": sorted(
            REQUIRED_ANALYTICS_CAPABILITIES
        ),
        "optional_capabilities": sorted(
            OPTIONAL_ANALYTICS_CAPABILITIES
        ),
        "notes": [
            "AUGUR has no live-postings provider configured.",
            "Missing live-postings evidence is not interpreted as zero employer demand.",
            "Live-postings evidence must remain separate from EURES, Eurostat, Cedefop STAS and ESCO taxonomy evidence.",
            "A provider must meet the contract before its data can be used in CareerFit context.",
        ],
    }


def validate_live_postings_snapshot(snapshot: dict) -> dict:
    provider_id = str(snapshot.get("provider_id") or "").strip()
    if not provider_id:
        raise ValueError("live postings snapshot requires provider_id")

    retrieved_at = snapshot.get("retrieved_at")
    if isinstance(retrieved_at, datetime):
        retrieved_at = retrieved_at.isoformat()
    elif retrieved_at is not None:
        retrieved_at = str(retrieved_at)

    posting_count = snapshot.get("posting_count")
    if posting_count is None:
        raise ValueError("live postings snapshot requires posting_count")
    posting_count = int(posting_count)
    if posting_count < 0:
        raise ValueError("posting_count must be non-negative")

    skills = snapshot.get("skills", [])
    languages = snapshot.get("languages", [])
    if skills is None:
        skills = []
    if languages is None:
        languages = []
    if not isinstance(skills, list) or not isinstance(languages, list):
        raise ValueError("skills and languages must be lists")

    return {
        "status": "available",
        "contract_version": LIVE_POSTINGS_CONTRACT_VERSION,
        "provider_id": provider_id,
        "retrieved_at": retrieved_at,
        "country_iso3": str(snapshot.get("country_iso3") or "").upper() or None,
        "region_code": snapshot.get("region_code"),
        "occupation_label": snapshot.get("occupation_label"),
        "isco08": snapshot.get("isco08"),
        "lookback_days": (
            int(snapshot["lookback_days"])
            if snapshot.get("lookback_days") is not None
            else None
        ),
        "posting_count": posting_count,
        "skills": skills,
        "languages": languages,
        "salary_context": snapshot.get("salary_context"),
        "posting_trend": snapshot.get("posting_trend"),
        "role": "context_only",
        "notes": [
            "Live postings are contextual employer-demand evidence, not a job-finding probability.",
            "Provider coverage, deduplication and extraction methodology must remain explicit.",
        ],
    }


def live_postings_provider_status() -> dict:
    return {
        "configured": False,
        "provider_id": None,
        "contract_version": LIVE_POSTINGS_CONTRACT_VERSION,
        "required_capabilities": sorted(
            REQUIRED_ANALYTICS_CAPABILITIES
        ),
        "optional_capabilities": sorted(
            OPTIONAL_ANALYTICS_CAPABILITIES
        ),
        "blocking": False,
        "reason": "no_provider_configured",
    }
