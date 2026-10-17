"""Source evidence must not certify partial or malformed official data."""
import copy
import pytest
from app.ingestion.eea_air_quality import inspect_eea_pm25
from app.ingestion.eurostat_geography_discovery import observed_geo_codes
from app.ingestion.eurostat import EurostatAdapter
from app.ingestion.eurostat_regional_sector import normalize_regional_sector_employment


class EEAResponse:
    def __init__(self, payload): self.payload=payload
    def raise_for_status(self): pass
    def json(self): return self.payload


class EEAClient:
    def __init__(self,payload): self.payload=payload
    def get(self,*args,**kwargs): return EEAResponse(self.payload)


def station(country, value=6.0):
    return {"attributes":{"country_iso_code":country,"statistics_year":2025,
        "station_longitude_deg":-8.0,"station_latitude_deg":42.0,"statistic_value":value,
        "measurement_unit":"ug/m3"}}


def test_partial_eea_page_cannot_be_aggregation_ready():
    result=inspect_eea_pm25(EEAClient({"features":[station("ES"),station("PT"),station("IE")],
        "exceededTransferLimit":True}))
    assert result["potentially_truncated"] is True
    assert result["ready_for_aggregation_design"] is False


def test_complete_eea_sample_may_be_ready_for_design():
    result=inspect_eea_pm25(EEAClient({"features":[station("ES"),station("PT"),station("IE")],
        "exceededTransferLimit":False}))
    assert result["potentially_truncated"] is False
    assert result["ready_for_aggregation_design"] is True


def test_nonfinite_eea_value_rejected():
    with pytest.raises(ValueError,match="finite"):
        inspect_eea_pm25(EEAClient({"features":[station("ES",float("nan"))]}))


def sparse_payload():
    return {"id":["geo","time"],"size":[1,1],"dimension":{
        "geo":{"category":{"index":{"ES11":0}}},
        "time":{"category":{"index":{"2025":0}}}},
        "value":{"0":9.5}}


@pytest.mark.parametrize("change",[
    lambda d: d.update(value="bad"),
    lambda d: d.update(size=[True,1]),
    lambda d: d.update(id=["geo","geo"]),
])
def test_malformed_geography_data_not_counted_as_observed(change):
    payload=sparse_payload()
    change(payload)
    assert observed_geo_codes(payload)==set()


def test_valid_sparse_eurostat_observation():
    assert observed_geo_codes(sparse_payload())=={"ES11"}


def sector_payload(value=10.0):
    return {"id":["geo","nace_r2","time"],"size":[1,1,1],
       "dimension":{"geo":{"category":{"index":{"ES11":0}}},
                    "nace_r2":{"category":{"index":{"J":0}}},
                    "time":{"category":{"index":{"2025":0}}}},
       "value":[value]}


@pytest.mark.parametrize("value",[True,"10",float("nan"),float("inf")])
def test_invalid_sector_value_rejected(value):
    adapter=EurostatAdapter(client=None)
    try:
        with pytest.raises(ValueError,match="Invalid sector observation"):
            normalize_regional_sector_employment(adapter,sector_payload(value))
    finally:
        adapter.close()


def test_sector_cardinality_mismatch_rejected():
    payload=sector_payload()
    payload["size"]=[2,1,1]
    adapter=EurostatAdapter(client=None)
    try:
        with pytest.raises(ValueError,match="cardinality mismatch"):
            normalize_regional_sector_employment(adapter,payload)
    finally:
        adapter.close()
