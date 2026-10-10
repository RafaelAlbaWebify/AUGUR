from app.services.global_evidence_contract import EvidenceContract, coverage_matrix


def test_worldwide_membership_no_inheritance_or_missing_as_zero():
    c = EvidenceContract("housing_cost", "percent", ("region",), "EUROSTAT", "dataset", "NUTS_2024")
    geos = [
        {"country_iso3": "ESP", "geo_code": "ES11", "geo_level": "region", "geography_system": "NUTS_2024"},
        {"country_iso3": "JPN", "geo_code": "JP13", "geo_level": "region", "geography_system": "OECD_TL2"},
        {"country_iso3": "ESP", "geo_code": "ES001C", "geo_level": "city", "geography_system": "URBAN_AUDIT_2024"},
    ]
    obs = [{"indicator_id": "housing_cost", "geo_code": "ES11", "geo_level": "region", "geography_system": "NUTS_2024", "unit": "percent", "source_id": "EUROSTAT", "dataset_id": "dataset", "period": 2025, "value": 0.0}]
    output = coverage_matrix([c], obs, geos)
    assert len(output) == 1
    assert output[0]["status"] == "observed"
    assert output[0]["periods"] == [2025]


def test_wrong_unit_is_rejected_not_silently_accepted():
    c = EvidenceContract("rent", "eur_per_month", ("city",), "OFFICIAL", "rents")
    geos = [{"country_iso3": "CAN", "geo_code": "TOR", "geo_level": "city", "geography_system": "LOCAL"}]
    obs = [{"indicator_id": "rent", "geo_code": "TOR", "geo_level": "city", "geography_system": "LOCAL", "unit": "eur_per_sqm", "source_id": "OFFICIAL", "dataset_id": "rents", "period": 2024, "value": 21}]
    assert coverage_matrix([c], obs, geos)[0]["status"] == "incompatible"
