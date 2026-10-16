"""GR-2: provider-returned dimensions and quality flag survive normalisation."""
import json
from app.ingestion.eurostat import EurostatAdapter
from app.services.regional_evidence import _latest_regional_indicator, REGIONAL_INDICATORS


def payload(status="e"):
    cats = {
        "geo": "ES11", "freq": "A", "age": "Y20-64",
        "sex": "T", "unit": "PC", "time": "2025",
    }
    return {
        "id": list(cats), "size": [1] * len(cats),
        "dimension": {
            k: {"category": {"index": {v: 0}, "label": {v: v}}}
            for k, v in cats.items()
        },
        "value": {"0": 7.2},
        "status": {"0": status},
        "updated": "2026-09-10",
    }


def test_source_tuple_and_status_retained():
    adapter = EurostatAdapter()
    try:
        rows = adapter.normalize(
            "ES11", {"indicator_id": "regional_employment_rate",
                     "dataset_id": "lfst_r_lfe2emprt", "unit": "percent"},
            payload(),
        )
    finally:
        adapter.close()
    assert len(rows) == 1
    assert rows[0]["source_dimensions"]["age"] == "Y20-64"
    assert rows[0]["source_dimensions"]["geo"] == "ES11"
    assert rows[0]["source_observation_status"] == "e"


class Stub:
    def fetch_dataset(self, *_):
        return payload()

    def normalize(self, geo, config, source):
        return [{"period": 2025, "value": 7.2, "source_dimensions": {
            "geo": geo, "age": "Y20-64", "unit": "PC"
        }, "source_observation_status": "e"}]


def test_regional_sync_passes_source_metadata():
    cfg = next(x for x in REGIONAL_INDICATORS if x["indicator_id"] == "regional_employment_rate")
    row = _latest_regional_indicator(Stub(), "ES11", cfg)
    assert json.loads(row["response_dimensions_json"])["age"] == "Y20-64"
    assert row["source_observation_status"] == "e"
