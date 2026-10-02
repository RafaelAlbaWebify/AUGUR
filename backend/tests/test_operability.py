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
):
    return {
        "country_iso3": iso3,
        "observed_rows": observed_rows,
        "observed_indicators": observed_indicators,
        "latest_observed_period": 2025 if observed_rows else None,
        "official_forecast_rows": official_forecast_rows,
        "source_count": len(source_ids or []) if observed_rows else 0,
        "source_ids": source_ids or [],
        "labour_earnings": {
            "country_iso3": iso3,
            "row_count": earnings_rows,
            "isco_group_count": earnings_groups,
            "latest_period": 2022 if earnings_rows else None,
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


def _provider_ids():
    return ["WORLD_BANK", "EUROSTAT", "OECD", "IMF", "UN_WPP"]


def test_operability_analysis_ready_still_blocks_without_temporal_model(monkeypatch):
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

    result = module.operability_status()

    assert result["status"] == "partial"
    assert result["analysis_ready"] is True
    assert result["ttv_temporal_model_ready"] is False
    assert result["ready"] is False
    assert result["blockers"] == ["ttv_temporal_model"]


def test_operability_ready_requires_validated_temporal_model(monkeypatch):
    monkeypatch.setattr(module, "providers_for_country", _all_providers)
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
