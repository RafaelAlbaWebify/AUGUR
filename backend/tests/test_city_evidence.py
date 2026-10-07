import pytest

from app.services.city_evidence import city_evidence


@pytest.fixture(autouse=True)
def _city_history_stub(monkeypatch):
    from app.services import city_evidence as module
    monkeypatch.setattr(
        module,
        "subnational_indicator_series",
        lambda code, max_points=8: [],
    )


class FakeAdapter:
    def fetch_dataset(self, dataset_id, filters):
        assert dataset_id == "urb_cpop1"
        assert filters["cities"] == "ES001C"
        assert filters["indic_ur"] == "DE1001V"
        return {"ok": True}

    def normalize(self, city_code, config, payload):
        assert city_code == "ES001C"
        return [
            {
                "period": 2024,
                "value": 3200000.0,
                "source_updated_at": "2026-10-02",
            },
            {
                "period": 2025,
                "value": 3250000.0,
                "source_updated_at": "2026-10-02",
            },
        ]


def test_city_evidence_returns_latest_population():
    result = city_evidence("ES001C", adapter=FakeAdapter())

    assert result["city_code"] == "ES001C"
    assert result["geo_level"] == "city"
    assert result["minimum_population_scope"] == 50000
    assert result["available_count"] == 1
    assert result["indicators"][0]["period"] == 2025
    assert result["indicators"][0]["value"] == 3250000.0


def test_refresh_city_pm25_stores_verified_observation(monkeypatch):
    from app.services import city_evidence as module

    stored = []

    monkeypatch.setattr(
        module,
        "resolve_eea_city",
        lambda code: {
            "city_code": code,
            "country_code": "ES",
            "eea_city_name": "Oviedo",
            "gisco_city_name": "Oviedo",
        },
    )
    monkeypatch.setattr(
        module,
        "fetch_city_pm25_annual",
        lambda city_name, country_code, year: {
            "status": "available",
            "year": 2024,
            "value": 9.0111,
            "unit": "ug_m3",
            "source_id": "EEA",
            "dataset_id": "EEA_AIR_QUALITY_E1A_CITY_MEASUREMENTS",
        },
    )
    monkeypatch.setattr(
        module,
        "upsert_subnational_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    assert module._refresh_city_pm25("ES013C") is True
    assert len(stored) == 1
    assert stored[0]["indicator_id"] == "city_pm25_annual_mean_observed"
    assert stored[0]["period"] == 2024
    assert stored[0]["value"] == 9.0111
    assert stored[0]["source_id"] == "EEA"
    assert stored[0]["source_updated_at"] is None


def test_local_city_result_combines_population_and_pm25():
    from app.services.city_evidence import _city_result_from_local

    result = _city_result_from_local(
        "ES013C",
        [
            {
                "indicator_id": "city_population",
                "period": 2024,
                "value": 220000,
                "unit": "persons",
                "dataset_id": "urb_cpop1",
                "source_id": "EUROSTAT",
                "source_updated_at": "2026-01-01",
            },
            {
                "indicator_id": "city_pm25_annual_mean_observed",
                "period": 2024,
                "value": 9.0111,
                "unit": "ug_m3",
                "dataset_id": "EEA_AIR_QUALITY_E1A_CITY_MEASUREMENTS",
                "source_id": "EEA",
                "source_updated_at": None,
            },
        ],
    )

    assert result is not None
    assert result["indicator_count"] == 2
    assert result["available_count"] == 2
    assert result["complete"] is True
    pm25 = next(
        item for item in result["indicators"]
        if item["indicator_id"] == "city_pm25_annual_mean_observed"
    )
    assert pm25["value"] == 9.0111
    assert pm25["source_id"] == "EEA"


def test_interactive_city_read_never_calls_external_providers(monkeypatch):
    from app.services import city_evidence as module

    monkeypatch.setattr(
        module,
        "latest_subnational_observations",
        lambda code: [],
    )
    module._CITY_CACHE.clear()

    class ForbiddenAdapter:
        def __init__(self, *args, **kwargs):
            raise AssertionError("interactive city read must not create Eurostat adapter")

    monkeypatch.setattr(module, "EurostatAdapter", ForbiddenAdapter)
    monkeypatch.setattr(
        module,
        "_refresh_city_pm25",
        lambda code: (_ for _ in ()).throw(
            AssertionError("interactive city read must not refresh EEA")
        ),
    )

    result = module.city_evidence("ES013C")

    assert result["available_count"] == 0
    assert result["indicator_count"] == 2
    assert all(item["reason"] == "not_cached" for item in result["indicators"])


def test_local_city_result_includes_history(monkeypatch):
    from app.services import city_evidence as module

    monkeypatch.setattr(
        module,
        "subnational_indicator_series",
        lambda code, max_points=8: [
            {
                "indicator_id": "city_population",
                "period": 2023,
                "value": 218000,
            },
            {
                "indicator_id": "city_population",
                "period": 2024,
                "value": 220000,
            },
        ],
    )

    result = module._city_result_from_local(
        "ES013C",
        [{
            "indicator_id": "city_population",
            "period": 2024,
            "value": 220000,
            "unit": "persons",
            "dataset_id": "urb_cpop1",
            "source_id": "EUROSTAT",
            "source_updated_at": "2026-01-01",
        }],
    )

    population = next(
        item for item in result["indicators"]
        if item["indicator_id"] == "city_population"
    )
    assert population["history"] == [
        {"period": 2023, "value": 218000},
        {"period": 2024, "value": 220000},
    ]
