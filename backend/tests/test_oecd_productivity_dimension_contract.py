"""Provider semantics: GDP/hour observations may not be relabeled from another OECD series."""
import pytest
from app.ingestion.oecd import OECDAdapter

BASE = (
    "REF_AREA,FREQ,MEASURE,ACTIVITY,UNIT_MEASURE,PRICE_BASE,"
    "TRANSFORMATION,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n"
    "ESP,A,GDPHRS,_T,USD_PPP_H,LR,N,2025,57.2,A\n"
)


def normalize(text):
    adapter=OECDAdapter(client=None)
    try:
        return adapter.normalize("ESP", text)
    finally:
        adapter.close()


def test_valid_source_tuple_preserved():
    rows=normalize(BASE)
    assert len(rows)==1
    assert rows[0]["indicator_id"]=="gdp_per_hour_worked"
    assert rows[0]["value"]==57.2


@pytest.mark.parametrize("before,after",[
    ("ESP,A,GDPHRS", "PRT,A,GDPHRS"),
    ("ESP,A,GDPHRS", "ESP,A,GDP"),
    ("USD_PPP_H", "USD"),
    (",LR,N,", ",N,N,"),
    (",LR,N,", ",LR,Y,"),
    ("ESP,A,GDPHRS", "ESP,Q,GDPHRS"),
])
def test_wrong_country_metric_unit_or_frequency_rejected(before,after):
    with pytest.raises(ValueError,match="source dimension mismatch"):
        normalize(BASE.replace(before,after))


def test_missing_contract_column_rejected():
    with pytest.raises(ValueError,match="missing required source dimensions"):
        normalize("TIME_PERIOD,OBS_VALUE\n2025,57.2\n")
