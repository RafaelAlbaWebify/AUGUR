"""Adversarial evidence integrity for all specialized Eurostat adapters."""
import copy
import pytest
from app.ingestion.eurostat import EurostatAdapter


CASES=[
    ("normalize_earnings",["geo","isco08","time"],["ES","OC251","2025"]),
    ("normalize_net_earnings",["geo","ecase","time"],["ES","P1_NCH_AW100","2025"]),
    ("normalize_job_vacancy_rates",["geo","isco08","time"],["ES","OC251","2025"]),
    ("normalize_job_transitions",["geo","age","duration","time"],["ES","Y15-74","TOTAL","2025"]),
]


def make_payload(ids,codes,value):
    return {"id":ids,"size":[1]*len(ids),
      "dimension":{k:{"category":{"index":{v:0}}} for k,v in zip(ids,codes)},
      "value":[value]}


@pytest.mark.parametrize("method,ids,codes",CASES)
@pytest.mark.parametrize("bad",[True,float("nan"),float("inf"),"10.0"])
def test_specialized_numeric_values_rejected(method,ids,codes,bad):
    adapter=EurostatAdapter()
    try:
        with pytest.raises(ValueError,match="Invalid .*source observation"):
            getattr(adapter,method)("ESP",make_payload(ids,codes,bad))
    finally:
        adapter.close()


@pytest.mark.parametrize("method,ids,codes",CASES)
def test_specialized_category_cardinality_fail_closed(method,ids,codes):
    adapter=EurostatAdapter()
    payload=make_payload(ids,codes,1.0)
    payload["size"][0]=2
    try:
        with pytest.raises(ValueError,match="cardinality mismatch"):
            getattr(adapter,method)("ESP",payload)
    finally:
        adapter.close()


@pytest.mark.parametrize("method,ids,codes",CASES)
def test_specialized_valid_numeric_values_preserved(method,ids,codes):
    adapter=EurostatAdapter()
    try:
        rows=getattr(adapter,method)("ESP",make_payload(ids,codes,1.75))
    finally:
        adapter.close()
    assert len(rows)==1
