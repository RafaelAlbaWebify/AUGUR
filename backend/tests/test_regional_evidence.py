from app.services import regional_evidence as regional_module
from app.services.regional_evidence import (
    REGIONAL_INDICATORS,
    NUTS3_SAFETY_INDICATORS,
    geographic_level,
    regional_comparison,
    regional_evidence,
)


class FakeAdapter:
    def fetch_dataset(self, dataset_id, filters):
        return {
            "dataset_id": dataset_id,
            "geo": filters["geo"],
        }

    def normalize(self, geo_code, config, payload):
        base = float(len(config["indicator_id"]))
        return [
            {
                "period": 2023,
                "value": base,
                "source_updated_at": "2026-01-01",
            },
            {
                "period": 2024,
                "value": base + 1,
                "source_updated_at": "2026-09-01",
            },
        ]


def test_geographic_level_recognises_nuts2_and_nuts3():
    assert geographic_level("ES11") == "nuts2"
    assert geographic_level("ES111") == "nuts3"
    assert geographic_level("ES") == "unknown"


def test_regional_evidence_returns_latest_available_values():
    result = regional_evidence("ES11", adapter=FakeAdapter())

    assert result["geo_code"] == "ES11"
    assert result["geo_level"] == "nuts2"
    assert result["indicator_count"] == len(REGIONAL_INDICATORS)
    assert result["available_count"] == len(REGIONAL_INDICATORS)
    assert result["complete"] is True
    assert {item["period"] for item in result["indicators"]} == {2024}
    assert {item["source_id"] for item in result["indicators"]} == {"EUROSTAT"}


def test_regional_comparison_keeps_region_codes_separate():
    result = regional_comparison(
        ["ES11", "PT11"],
        adapter=FakeAdapter(),
    )

    assert result["regions"] == [
        {"geo_code": "ES11", "geo_level": "nuts2"},
        {"geo_code": "PT11", "geo_level": "nuts2"},
    ]
    assert result["indicator_count"] == len(REGIONAL_INDICATORS)
    for indicator in result["indicators"]:
        assert set(indicator["regions"]) == {"ES11", "PT11"}



def test_regional_gdp_query_uses_dataset_dimensions_only():
    gdp = next(
        item for item in REGIONAL_INDICATORS
        if item["indicator_id"] == "regional_gdp_per_capita"
    )

    assert gdp["dataset_id"] == "nama_10r_3gdp"
    assert gdp["filters"] == {
        "freq": "A",
        "unit": "EUR_HAB",
    }


def test_regional_evidence_exposes_sector_structure(monkeypatch):
    monkeypatch.setattr(
        regional_module,
        "latest_subnational_observations",
        lambda code: [
            {
                "indicator_id": "regional_employment_rate",
                "period": 2025,
                "value": 72.0,
                "unit": "percent",
                "dataset_id": "lfst_r_lfe2emprt",
                "source_id": "EUROSTAT",
                "source_updated_at": "2026-09-10",
            }
        ],
    )
    monkeypatch.setattr(
        regional_module,
        "latest_regional_sector_employment_for_geo",
        lambda code: [
            {
                "geo_code": code,
                "period": 2025,
                "nace_code": "TOTAL",
                "nace_label": "Total",
                "employment_thousands": 400.0,
                "source_id": "EUROSTAT",
                "dataset_id": "lfst_r_lfe2en2",
            },
            {
                "geo_code": code,
                "period": 2025,
                "nace_code": "J",
                "nace_label": "Information and communication",
                "employment_thousands": 40.0,
                "source_id": "EUROSTAT",
                "dataset_id": "lfst_r_lfe2en2",
            },
            {
                "geo_code": code,
                "period": 2025,
                "nace_code": "C",
                "nace_label": "Manufacturing",
                "employment_thousands": 80.0,
                "source_id": "EUROSTAT",
                "dataset_id": "lfst_r_lfe2en2",
            },
        ],
    )

    result = regional_evidence("ES12")

    assert result["sector_structure"]["status"] == "available"
    assert result["sector_structure"]["period"] == 2025
    assert result["sector_structure"]["top_sectors"][0]["nace_code"] == "C"
    ict = next(
        item for item in result["sector_structure"]["top_sectors"]
        if item["nace_code"] == "J"
    )
    assert ict["employment_share_pct"] == 10.0


def test_regional_comparison_includes_sector_structure(monkeypatch):
    def fake_region(code, adapter=None):
        share = 8.0 if code == "ES11" else 5.0
        return {
            "geo_code": code,
            "geo_level": "nuts2",
            "indicators": [],
            "sector_structure": {
                "status": "available",
                "top_sectors": [
                    {
                        "nace_code": "J",
                        "nace_label": "Information and communication",
                        "period": 2025,
                        "employment_thousands": 20.0,
                        "employment_share_pct": share,
                    }
                ],
            },
        }

    monkeypatch.setattr(regional_module, "regional_evidence", fake_region)

    result = regional_comparison(["ES11", "ES12"])

    assert result["sector_comparison"]["status"] == "available"
    sector = result["sector_comparison"]["sectors"][0]
    assert sector["nace_code"] == "J"
    assert sector["regions"]["ES11"]["employment_share_pct"] == 8.0
    assert sector["regions"]["ES12"]["employment_share_pct"] == 5.0
    assert result["sector_comparison"]["role"] == "regional_employment_structure_only"


def test_nuts3_uses_only_safety_indicators():
    result = regional_evidence("ES120", adapter=FakeAdapter())

    assert result["geo_level"] == "nuts3"
    assert result["indicator_count"] == len(NUTS3_SAFETY_INDICATORS)
    assert {
        item["indicator_id"] for item in result["indicators"]
    } == {
        "regional_intentional_homicide_rate",
        "regional_robbery_rate",
    }


def test_access_indicator_queries_use_exact_eurostat_dimensions():
    internet = next(
        item for item in REGIONAL_INDICATORS
        if item["indicator_id"] == "regional_household_internet_access"
    )
    air = next(
        item for item in REGIONAL_INDICATORS
        if item["indicator_id"] == "regional_air_passengers_thousands"
    )

    assert internet["dataset_id"] == "isoc_r_iacc_h"
    assert internet["filters"] == {
        "freq": "A",
        "unit": "PC_HH",
    }
    assert air["dataset_id"] == "tran_r_avpa_nm"
    assert air["filters"] == {
        "freq": "A",
        "tra_meas": "PAS_CRD",
        "unit": "THS_PAS",
    }


def test_safety_indicators_are_rates_not_counts():
    assert {
        item["filters"]["unit"]
        for item in NUTS3_SAFETY_INDICATORS
    } == {"P_HTHAB"}
    assert {
        item["filters"]["iccs"]
        for item in NUTS3_SAFETY_INDICATORS
    } == {"ICCS0101", "ICCS0401"}


def test_local_partial_region_is_served_without_network_enrichment(monkeypatch):
    calls = {"adapter_created": 0}

    monkeypatch.setattr(
        regional_module,
        "latest_subnational_observations",
        lambda code: [
            {
                "indicator_id": "regional_employment_rate",
                "period": 2025,
                "value": 72.0,
                "unit": "percent",
                "dataset_id": "lfst_r_lfe2emprt",
                "source_id": "EUROSTAT",
                "source_updated_at": "2026-09-10",
            }
        ],
    )

    class ForbiddenAdapter:
        def __init__(self, *args, **kwargs):
            calls["adapter_created"] += 1
            raise AssertionError("interactive regional reads must not create a network adapter")

    monkeypatch.setattr(regional_module, "EurostatAdapter", ForbiddenAdapter)
    monkeypatch.setattr(
        regional_module,
        "latest_regional_sector_employment_for_geo",
        lambda code: [],
    )
    regional_module._REGIONAL_CACHE.clear()

    result = regional_evidence("ES12")

    assert result["available_count"] == 1
    assert result["complete"] is False
    assert calls["adapter_created"] == 0
    unavailable = {
        item["indicator_id"]
        for item in result["indicators"]
        if item["status"] == "unavailable"
    }
    assert "regional_household_internet_access" in unavailable
    assert "regional_air_passengers_thousands" in unavailable


def test_regional_evidence_exposes_environmental_health_separately(monkeypatch):
    monkeypatch.setattr(
        regional_module,
        "latest_subnational_observations",
        lambda code: [
            {
                "indicator_id": "regional_employment_rate",
                "period": 2025,
                "value": 72.0,
                "unit": "percent",
                "dataset_id": "lfst_r_lfe2emprt",
                "source_id": "EUROSTAT",
                "source_updated_at": "2026-09-10",
            }
        ],
    )
    monkeypatch.setattr(
        regional_module,
        "latest_regional_sector_employment_for_geo",
        lambda code: [],
    )
    monkeypatch.setattr(
        regional_module,
        "latest_environmental_health_burden_for_geo",
        lambda code: [
            {
                "geo_code": code,
                "geo_level": "NUTS2",
                "period": 2023,
                "burden_type": "PMD",
                "burden_label": "Premature deaths - Premature deaths",
                "value": 812.0,
                "unit_code": "NR",
                "unit_label": "Number",
                "obs_status": None,
                "source_id": "EEA",
                "dataset_id": "EEA_PM25_PREMATURE_DEATHS_NUTS23",
                "dataset_version": "eea-test-v1",
            },
            {
                "geo_code": code,
                "geo_level": "NUTS2",
                "period": 2023,
                "burden_type": "YLL",
                "burden_label": "Premature deaths - Years of life lost",
                "value": 9634.0,
                "unit_code": "NR",
                "unit_label": "Number",
                "obs_status": "e",
                "source_id": "EEA",
                "dataset_id": "EEA_PM25_PREMATURE_DEATHS_NUTS23",
                "dataset_version": "eea-test-v1",
            },
        ],
    )
    regional_module._REGIONAL_CACHE.clear()

    result = regional_evidence("ES12")

    health = result["environmental_health"]
    assert health["status"] == "available"
    assert health["source_id"] == "EEA"
    assert health["period"] == 2023
    assert {item["burden_type"] for item in health["metrics"]} == {"PMD", "YLL"}
    assert any("not a measurement" in note for note in health["notes"])
