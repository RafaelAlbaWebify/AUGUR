from app.services.housing_affordability import housing_affordability_evidence


def test_real_official_metadata_kept_separate_without_inventing_rent():
    result = housing_affordability_evidence([
        {"indicator_id": "regional_housing_cost_overburden_rate", "status": "available", "unit": "percent", "value": 12.5, "period": 2025, "source_id": "EUROSTAT", "dataset_id": "ilc_lvho07_r"},
        {"indicator_id": "regional_disposable_income_pps_per_capita", "status": "available", "unit": "pps_per_person", "value": 23000, "period": 2023, "source_id": "EUROSTAT", "dataset_id": "nama_10r_2hhinc"},
    ])
    assert result["housing_cost_overburden"]["value_pct"] == 12.5
    assert result["disposable_income_pps_per_capita"]["period"] == 2023
    assert result["rent_to_net_income_pct"] is None
    assert not result["affordability_complete"]


def test_wrong_units_or_missing_values_are_not_used():
    result = housing_affordability_evidence([
        {"indicator_id": "regional_housing_cost_overburden_rate", "status": "available", "unit": "pps_per_person", "value": 11},
        {"indicator_id": "regional_disposable_income_pps_per_capita", "status": "unavailable", "unit": "pps_per_person"},
    ])
    assert result["status"] == "unavailable"
    assert result["housing_cost_overburden"]["value_pct"] is None
