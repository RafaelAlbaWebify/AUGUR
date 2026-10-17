"""Regression: every reported World Bank data page must be present and valid."""
import pytest
from app.ingestion.world_bank import WorldBankAdapter


class Response:
    def __init__(self, data): self.data=data
    def raise_for_status(self): return None
    def json(self): return self.data


class Client:
    def __init__(self, second): self.second=second
    def get(self,url,params=None):
        if params.get("page")==2: return Response(self.second)
        return Response([{"pages":2,"page":1},[{"date":"2025","value":10}]])


@pytest.mark.parametrize("second",[
    {"error":"permission denied"},
    [{},None],
    [{"page":3},[{"date":"2024","value":20}]],
])
def test_missing_or_malformed_second_page_rejected(second):
    adapter=WorldBankAdapter(client=Client(second),max_retries=1)
    with pytest.raises(ValueError,match="Invalid World Bank response page 2"):
        adapter.fetch_indicator_many(["ESP"],"NY.GDP.MKTP.CD")


def test_valid_second_page_combines_only_verified_data():
    adapter=WorldBankAdapter(client=Client([{"page":2},[{"date":"2024","value":20}]]),max_retries=1)
    _,observations=adapter.fetch_indicator_many(["ESP"],"NY.GDP.MKTP.CD")
    assert len(observations)==2
