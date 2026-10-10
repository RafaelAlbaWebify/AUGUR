import pytest
from app.ingestion.eurostat_regional_labour import normalize_subnational
from app.ingestion.eurostat import EurostatAdapter

PAYLOAD = {
  "id":["geo","time"], "size":[3,1],
  "dimension":{
    "geo":{"category":{"index":{"ES11":0,"BG31":1,"FR10":2},"label":{"BG31":"Severozapaden"}}},
    "time":{"category":{"index":{"2025":0}}}
  },
  "value":[10,11,12], "updated":"2026-10-10"
}
CONFIG={"indicator_id":"regional_employment_rate","dataset_id":"lfst_r_lfe2emprt","unit":"percent"}

def test_dynamic_country_scope_and_pilot_compatibility():
    adapter=EurostatAdapter()
    try:
        assert [r["geo_code"] for r in normalize_subnational(adapter, CONFIG, PAYLOAD)] == ["ES11"]
        assert [r["geo_code"] for r in normalize_subnational(adapter, CONFIG, PAYLOAD, {"BG","FR"})] == ["BG31","FR10"]
        assert normalize_subnational(adapter, CONFIG, PAYLOAD, set()) == []
    finally:
        adapter.close()

def test_reject_invalid_country_scope():
    adapter=EurostatAdapter()
    try:
        with pytest.raises(ValueError, match="ISO2"):
            normalize_subnational(adapter, CONFIG, PAYLOAD, {"BGR"})
    finally:
        adapter.close()
