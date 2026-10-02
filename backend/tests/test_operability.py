from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services import operability as module


def _country(
    iso3: str,
    observed_rows: int,
    observed_indicators: int,
    official_forecast_rows: int,
    earnings_rows: int,
    earnings_groups: int,
    source_ids: list[str] | None = None,
    retrieved_at=None,
):
    return {
        "country_iso3": iso3,
        "observed_rows": observed_rows,
        "observed_indicators": observed_indicators,
        "latest_observed_period": 2025 if observed_rows else None,
        "official_forecast_rows": official_forecast_rows,
        "source_count": len(source_ids or []) if observed_rows else 0,
        "source_ids": source_ids or [],
        "provider_retrieved_at": {
            source_id: (
                retrieved_at
                if retrieved_at is not None
                else datetime.now(timezone.utc)
            )
            for source_id in (source_ids or [])
        },
        "labour_earnings": {
            "country_iso3": iso3,
            "row_count": earnings_rows,
            "isco_group_count": earnings_groups,
            "latest_period": 2022 if earnings_rows else None,
            "latest_retrieved_at": (
                retrieved_at
                if retrieved_at is not None
                else datetime.now(timezone.utc)
            ) if earnings_rows else None,
        },
        "net_earnings": {
            "country_iso3": iso3,
            "row_count": 1 if earnings_rows else 0,
            "latest_period": 2025 if earnings_rows else None,
            "latest_retrieved_at": (
                retrieved_at
                if retrieved_at is not None
                else datetime.now(timezone.utc)
            ) if earnings_rows else None,
        },
        "job_transitions": {
            "country_iso3": iso3,
            "row_count": 4 if earnings_rows else 0,
            "age_group_count": 4 if earnings_rows else 0,
            "latest_period": 2025 if earnings_rows else None,
            "latest_retrieved_at": (
                retrieved_at
                if retrieved_at is not None
                else datetime.now(timezone.utc)
            ) if earnings_rows else None,
        },
    }


def _all_providers(_country_iso3: str):
    return [
        SimpleNamespace(provider_id="WORLD_BANK"),
        SimpleNamespace(provider_id="EUROSTAT"),
        SimpleNamespace(provider_id="OECD"),
        SimpleNamespace(provider_id="IMF"),
        SimpleNamespace(provider_id="UN_WPP"),
    ]


def _supported_temporal_validation():
    return {
        "engine_version": "test",
        "ready_for_versioning": True,
        "gates": {},
        "blockers": [],
        "experimental": [],
        "missing": [],
        "notes": [],
    }


def _provider_ids():
    return ["WORLD_BANK", "EUROSTAT", "OECD", "IMF", "UN_WPP"]


def test_operability_analysis_ready_still_blocks_without_temporal_model(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )
    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {
            "countries": [
                _country("ESP", 100, 18, 12, 9, 9, _provider_ids()),
                _country("IRL", 100, 18, 12, 9, 9, _provider_ids()),
                _country("PRT", 100, 18, 12, 9, 9, _provider_ids()),
            ]
        },
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "relation_count": 120000,
        },
    )

    result = module.operability_status()

    assert result["status"] == "partial"
    assert result["analysis_ready"] is True
    assert result["ttv_temporal_model_ready"] is False
    assert result["ready"] is False
    assert result["blockers"] == ["ttv_temporal_model"]


def test_operability_ready_requires_validated_temporal_model(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 100,
            "coverage_scope": "full_unit_group_coverage",
            "full_occupation_coverage": True,
            "notes": [],
        },
    )
    monkeypatch.setattr(module, "TEMPORAL_MODEL_VERSION", "ttv-temporal-v1")
    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {
            "countries": [
                _country("ESP", 100, 18, 12, 9, 9, _provider_ids()),
                _country("IRL", 100, 18, 12, 9, 9, _provider_ids()),
                _country("PRT", 100, 18, 12, 9, 9, _provider_ids()),
            ]
        },
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "relation_count": 120000,
        },
    )

    result = module.operability_status()

    assert result["status"] == "ready"
    assert result["analysis_ready"] is True
    assert result["ttv_temporal_model_ready"] is True
    assert result["ttv_temporal_model_version"] == "ttv-temporal-v1"
    assert result["ready"] is True
    assert result["blockers"] == []


def test_operability_partial_when_country_analysis_ready_but_esco_is_seed(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )
    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {
            "countries": [
                _country("ESP", 100, 18, 12, 9, 9, _provider_ids()),
                _country("IRL", 100, 18, 12, 9, 9, _provider_ids()),
                _country("PRT", 100, 18, 12, 9, 9, _provider_ids()),
            ]
        },
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "seed",
            "version": "1.2.1",
            "occupation_count": 2,
            "skill_count": 3,
            "relation_count": 4,
        },
    )

    result = module.operability_status()

    assert result["status"] == "partial"
    assert result["country_analysis_ready"] is True
    assert result["local_employment_evidence_ready"] is True
    assert result["esco_full_ready"] is False
    assert result["blockers"] == ["full_esco_dataset"]


def test_operability_partial_when_datastores_have_only_seed_esco(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )
    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {
            "countries": [
                _country("ESP", 0, 0, 0, 0, 0, []),
                _country("IRL", 0, 0, 0, 0, 0, []),
                _country("PRT", 0, 0, 0, 0, 0, []),
            ]
        },
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "seed",
            "version": "1.2.1",
            "occupation_count": 2,
            "skill_count": 3,
            "relation_count": 4,
        },
    )

    result = module.operability_status()

    assert result["status"] == "partial"
    assert result["country_analysis_ready"] is False
    assert "country_analysis_evidence" in result["blockers"]
    assert "local_employment_earnings" in result["blockers"]
    assert "full_esco_dataset" in result["blockers"]


def test_operability_empty_when_no_evidence_or_esco(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )
    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {
            "countries": [
                _country("ESP", 0, 0, 0, 0, 0),
                _country("IRL", 0, 0, 0, 0, 0),
                _country("PRT", 0, 0, 0, 0, 0),
            ]
        },
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "none",
            "version": "none",
            "occupation_count": 0,
            "skill_count": 0,
            "relation_count": 0,
        },
    )

    result = module.operability_status()

    assert result["status"] == "empty"
    assert result["ready"] is False


def test_operability_partial_when_a_configured_provider_is_missing(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )

    incomplete_sources = ["WORLD_BANK", "EUROSTAT", "OECD", "IMF"]
    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {
            "countries": [
                _country("ESP", 100, 18, 12, 9, 9, incomplete_sources),
                _country("IRL", 100, 18, 12, 9, 9, _provider_ids()),
                _country("PRT", 100, 18, 12, 9, 9, _provider_ids()),
            ]
        },
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "relation_count": 120000,
        },
    )

    result = module.operability_status()

    assert result["status"] == "partial"
    assert result["country_analysis_ready"] is False
    assert result["provider_coverage"]["ESP"]["complete"] is False
    assert result["provider_coverage"]["ESP"]["missing"] == ["UN_WPP"]
    assert "country_analysis_evidence" in result["blockers"]


def test_operability_partial_when_provider_sync_is_stale(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )

    stale_time = datetime.now(timezone.utc) - timedelta(days=45)
    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {
            "countries": [
                _country("ESP", 100, 18, 12, 9, 9, _provider_ids(), stale_time),
                _country("IRL", 100, 18, 12, 9, 9, _provider_ids()),
                _country("PRT", 100, 18, 12, 9, 9, _provider_ids()),
            ]
        },
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "relation_count": 120000,
        },
    )

    result = module.operability_status()

    assert result["status"] == "partial"
    assert result["data_sync_fresh"] is False
    assert result["provider_coverage"]["ESP"]["fresh"] is False
    assert set(result["provider_coverage"]["ESP"]["stale"]) == set(_provider_ids())
    assert "data_sync_stale" in result["blockers"]


def test_operability_partial_when_net_earnings_reference_is_missing(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )

    countries = [
        _country("ESP", 100, 18, 12, 9, 9, _provider_ids()),
        _country("IRL", 100, 18, 12, 9, 9, _provider_ids()),
        _country("PRT", 100, 18, 12, 9, 9, _provider_ids()),
    ]
    countries[0]["net_earnings"]["row_count"] = 0
    countries[0]["net_earnings"]["latest_period"] = None

    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {"countries": countries},
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "relation_count": 120000,
        },
    )

    result = module.operability_status()

    assert result["local_employment_evidence_ready"] is False
    assert "local_employment_earnings" in result["blockers"]


def test_operability_exposes_temporal_validation_blockers(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {
            "countries": [
                _country("ESP", 100, 18, 12, 9, 9, _provider_ids()),
                _country("IRL", 100, 18, 12, 9, 9, _provider_ids()),
                _country("PRT", 100, 18, 12, 9, 9, _provider_ids()),
            ]
        },
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "relation_count": 120000,
        },
    )
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        lambda: {
            "engine_version": "test",
            "ready_for_versioning": False,
            "gates": {
                "local_financial_transition": {
                    "state": "missing",
                    "reason": "not_modelled",
                }
            },
            "blockers": ["local_financial_transition"],
            "experimental": [],
            "missing": ["local_financial_transition"],
            "notes": [],
        },
    )

    result = module.operability_status()

    assert result["ttv_temporal_model_ready"] is False
    assert result["ttv_temporal_validation"]["ready_for_versioning"] is False
    assert result["ttv_temporal_validation"]["blockers"] == [
        "local_financial_transition"
    ]


def test_operability_partial_when_job_transition_evidence_is_missing(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )
    monkeypatch.setattr(module, "TEMPORAL_MODEL_VERSION", "ttv-temporal-v1")

    countries = [
        _country("ESP", 100, 18, 12, 9, 9, _provider_ids()),
        _country("IRL", 100, 18, 12, 9, 9, _provider_ids()),
        _country("PRT", 100, 18, 12, 9, 9, _provider_ids()),
    ]
    countries[0]["job_transitions"]["row_count"] = 0
    countries[0]["job_transitions"]["age_group_count"] = 0
    countries[0]["job_transitions"]["latest_period"] = None

    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {"countries": countries},
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "relation_count": 120000,
        },
    )

    result = module.operability_status()

    assert result["analysis_ready"] is True
    assert result["ttv_temporal_model_ready"] is True
    assert result["job_transition_evidence_ready"] is False
    assert result["ready"] is False
    assert "labour_job_transition_evidence" in result["blockers"]


def test_operability_rejects_stale_auxiliary_labour_evidence(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )

    countries = [
        _country("ESP", 100, 18, 12, 9, 9, _provider_ids()),
        _country("IRL", 100, 18, 12, 9, 9, _provider_ids()),
        _country("PRT", 100, 18, 12, 9, 9, _provider_ids()),
    ]
    stale_time = datetime.now(timezone.utc) - timedelta(days=45)
    countries[0]["labour_earnings"]["latest_retrieved_at"] = stale_time
    countries[0]["net_earnings"]["latest_retrieved_at"] = stale_time
    countries[0]["job_transitions"]["latest_retrieved_at"] = stale_time

    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {"countries": countries},
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "relation_count": 120000,
        },
    )

    result = module.operability_status()

    assert result["local_employment_evidence_ready"] is False
    assert result["job_transition_evidence_ready"] is False
    assert "local_employment_earnings" in result["blockers"]
    assert "labour_job_transition_evidence" in result["blockers"]


def test_operability_distinguishes_core_from_full_personal_fit_evidence(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
    monkeypatch.setattr(
        module,
        "temporal_model_validation_status",
        _supported_temporal_validation,
    )
    monkeypatch.setattr(
        module,
        "career_market_evidence_status",
        lambda: {
            "evidence_id": "test",
            "rule_version": "test",
            "report_year": 2025,
            "conditions_year": 2024,
            "supported_countries": ["ESP", "IRL", "PRT"],
            "broad_country_count": 3,
            "unit_group_count": 4,
            "coverage_scope": "partial_unit_group_coverage",
            "full_occupation_coverage": False,
            "notes": [],
        },
    )

    countries = [
        _country("ESP", 100, 18, 12, 9, 9, _provider_ids()),
        _country("IRL", 100, 18, 12, 9, 9, _provider_ids()),
        _country("PRT", 100, 18, 12, 9, 9, _provider_ids()),
    ]
    monkeypatch.setattr(
        module,
        "analytical_evidence_status",
        lambda: {"countries": countries},
    )
    monkeypatch.setattr(
        module,
        "esco_status",
        lambda: {
            "mode": "full",
            "version": "1.2.1",
            "occupation_count": 3000,
            "skill_count": 14000,
            "relation_count": 120000,
        },
    )

    result = module.operability_status()

    assert result["personal_fit_core_evidence_ready"] is True
    assert result["personal_fit_full_evidence_ready"] is False
    assert result["analysis_ready"] is True
    assert result["career_market_evidence"]["coverage_scope"] == "partial_unit_group_coverage"
