"""Repeated OECD population tuples may not silently overwrite a different series."""
import csv
import io
import pytest
from app.ingestion.oecd_regional import OECDRegionalAdapter


def payload(levels, values):
    buf=io.StringIO()
    writer=csv.DictWriter(buf,fieldnames=["TERRITORIAL_LEVEL","MEASURE","AGE","SEX","REF_AREA","COUNTRY","TIME_PERIOD","OBS_VALUE"])
    writer.writeheader()
    for level,value in zip(levels,values):
        writer.writerow({"TERRITORIAL_LEVEL":level,"MEASURE":"POP","AGE":"_T","SEX":"_T",
                         "REF_AREA":"AU203","COUNTRY":"AUS","TIME_PERIOD":"2022","OBS_VALUE":value})
    return buf.getvalue()


def normalize(text):
    adapter=OECDRegionalAdapter()
    try:
        return adapter.normalize_population(text,allowed_country_iso3={"AUS"})
    finally:
        adapter.close()


def test_exact_duplicate_collapses_without_changing_value():
    rows=normalize(payload(["TL2","TL2"],[100,100]))
    assert len(rows)==1
    assert rows[0]["value"]==100


@pytest.mark.parametrize("levels,values", [
    (["TL2","TL2"],[100,101]),
    (["TL2","TL3"],[100,100]),
])
def test_conflicting_duplicate_is_rejected(levels,values):
    with pytest.raises(ValueError,match="Conflicting OECD population source tuples"):
        normalize(payload(levels,values))
