import pytest

from app.ingestion.eurostat_nuts_registry import (
    assess_reconciled_live_coverage,
    extract_official_nuts2_codes,
    reconcile_nuts2024,
)


def test_only_explicit_gisco_nuts2_features_are_registered():
    data={"type":"FeatureCollection","features":[
        {"properties":{"NUTS_ID":"ES11","LEVL_CODE":2}},
        {"properties":{"NUTS_ID":"BG31","LEVL_CODE":2}},
    ]}
    assert extract_official_nuts2_codes(data) == {"ES11", "BG31"}
    with pytest.raises(ValueError,match="Unexpected"):
        extract_official_nuts2_codes({"type":"FeatureCollection","features":[{"properties":{"NUTS_ID":"ES1","LEVL_CODE":1}}]})


def test_reconciliation_preserves_observed_and_historical_membership():
    report={"scope":"dataset_geography","ready":True,"datasets":[{
        "status":"available","dataset_id":"example",
        "countries":{"ES":[{"geo_code":"ES11","observation_status":"observed"},
                           {"geo_code":"ES99","observation_status":"observed"}],
                     "BG":[{"geo_code":"BG31","observation_status":"no_numeric_observation"}]}
    }]}
    result=reconcile_nuts2024(report,{"ES11","BG31"})
    dataset=result["datasets"][0]
    assert dataset["official_nuts2024_region_count"]==2
    assert dataset["official_nuts2024_observed_region_count"]==1
    assert dataset["outside_nuts2024_count"]==1
    assert dataset["outside_nuts2024_observed_region_count"]==1
    assert dataset["countries"]["ES"][1]["nuts_2024_status"]=="not_in_nuts2_2024"
    assert result["registry_reconciled"] is True


def test_registry_failure_does_not_silently_approve_any_region():
    with pytest.raises(ValueError,match="empty"):
        reconcile_nuts2024({"datasets":[]},set())


def test_live_coverage_assessment_requires_observed_official_regions_per_dataset():
    report={
        "registry_reconciled":True,
        "nuts_registry":{"vintage":2024},
        "datasets":[
            {
                "dataset_id":"good",
                "status":"available",
                "official_nuts2024_observed_region_count":2,
                "outside_nuts2024_observed_region_count":1,
            },
            {
                "dataset_id":"empty",
                "status":"available",
                "official_nuts2024_observed_region_count":0,
            },
        ],
    }
    result=assess_reconciled_live_coverage(report)
    assert result["ready"] is False
    assert result["datasets"][0]["outside_nuts2024_observed_region_count"] == 1
    assert result["failures"] == ["empty: no observed official NUTS2 2024 regions"]


def test_live_coverage_assessment_rejects_unreconciled_report():
    with pytest.raises(ValueError,match="reconciled"):
        assess_reconciled_live_coverage({"datasets":[]})
