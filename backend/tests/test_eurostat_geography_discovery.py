from app.ingestion.eurostat_geography_discovery import (
    discover_dataset_geographies, discover_regional_dataset_coverage,
)


def test_discovers_nonpilot_nuts2_candidates_without_certifying_vintage():
    payload = {
        "dimension":{"geo":{"category":{"index":{"ES11":0,"BG31":1,"FR10":2,"ES":3,"EU27_2020":4},"label":{"BG31":"Severozapaden"}}}},
        "updated":"2026-10-10",
    }
    result = discover_dataset_geographies(payload, "sample")
    assert result["country_count"] == 3
    assert result["region_count"] == 3
    assert result["countries"]["BG"][0]["geo_name"] == "Severozapaden"
    assert result["classification_status"] == "dataset_member_not_verified_nuts_vintage"


def test_source_errors_are_reported_not_recast_as_missing_geographies():
    class Broken:
        def fetch_dataset(self, dataset_id, filters):
            raise RuntimeError("provider unavailable")
    report = discover_regional_dataset_coverage(Broken(), [{"dataset_id":"test","filters":{}}])
    assert report["ready"] is False
    assert report["datasets"][0]["status"] == "source_error"
