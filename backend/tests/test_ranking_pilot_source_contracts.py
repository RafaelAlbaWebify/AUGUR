"""Protect source dimensions of the first two ranking pilots."""
from app.services.ranking_eligibility import PILOT_CONTRACTS
from app.services.regional_evidence import REGIONAL_INDICATORS


def test_pilot_contracts_match_existing_eurostat_ingestion_filters():
    by_id = {item["indicator_id"]: item for item in REGIONAL_INDICATORS}
    assert set(PILOT_CONTRACTS) <= set(by_id)
    for identifier, contract in PILOT_CONTRACTS.items():
        config = by_id[identifier]
        assert config["dataset_id"] == contract.dataset_id
        assert config["unit"] == contract.unit == "percent"
        assert config["filters"] == {
            "freq": "A", "age": "Y20-64", "sex": "T", "unit": "PC",
        }
        assert contract.source_id == "EUROSTAT"
        assert contract.geography_system == "NUTS_2024"
        assert contract.geo_level == "nuts2"
