import pytest

from app.services.live_postings import (
    LivePostingsCapabilities,
    provider_not_configured_evidence,
    validate_live_postings_snapshot,
)


def test_unconfigured_provider_is_explicit_and_non_blocking_evidence():
    result = provider_not_configured_evidence()

    assert result["status"] == "provider_not_configured"
    assert result["provider_id"] is None
    assert result["role"] == "context_only"
    assert "active_posting_count" in result["requested_metrics"]
    assert "skill_demand_share" in result["requested_metrics"]


def test_core_capabilities_require_country_occupation_date_and_active_postings():
    complete = LivePostingsCapabilities(
        provider_id="test",
        capabilities=frozenset({
            "active_postings",
            "country_filter",
            "occupation_filter",
            "posting_date",
            "skills",
        }),
    )
    incomplete = LivePostingsCapabilities(
        provider_id="test",
        capabilities=frozenset({
            "active_postings",
            "country_filter",
            "posting_date",
        }),
    )

    assert complete.supports_core_analytics is True
    assert incomplete.supports_core_analytics is False


def test_snapshot_validation_keeps_live_evidence_contextual():
    result = validate_live_postings_snapshot({
        "provider_id": "test",
        "country_iso3": "irl",
        "occupation_label": "ICT support technician",
        "posting_count": 42,
        "lookback_days": 30,
        "skills": [{"label": "PowerShell", "share_pct": 31.0}],
        "languages": [{"label": "English", "share_pct": 84.0}],
    })

    assert result["status"] == "available"
    assert result["country_iso3"] == "IRL"
    assert result["posting_count"] == 42
    assert result["role"] == "context_only"


@pytest.mark.parametrize(
    "payload",
    [
        {"posting_count": 1},
        {"provider_id": "test"},
        {"provider_id": "test", "posting_count": -1},
        {"provider_id": "test", "posting_count": 1, "skills": {}},
    ],
)
def test_snapshot_validation_rejects_malformed_evidence(payload):
    with pytest.raises(ValueError):
        validate_live_postings_snapshot(payload)
