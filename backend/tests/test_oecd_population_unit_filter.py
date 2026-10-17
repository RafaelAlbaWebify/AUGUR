"""Live-source regression: OECD population and density have different units."""
import csv
import io
import pytest
from app.ingestion.oecd_regional import OECDRegionalAdapter


def source_rows(unit2="PS",multiplier2="0"):
    out=io.StringIO()
    keys=["TERRITORIAL_LEVEL","MEASURE","AGE","SEX","REF_AREA","COUNTRY","TIME_PERIOD","UNIT_MEASURE","UNIT_MULT","OBS_VALUE"]
    wr=csv.DictWriter(out,fieldnames=keys);wr.writeheader()
    base={"TERRITORIAL_LEVEL":"TL3","MEASURE":"POP","AGE":"_T","SEX":"_T",
          "REF_AREA":"AU203","COUNTRY":"AUS","TIME_PERIOD":"2022"}
    wr.writerow({**base,"UNIT_MEASURE":"PS_KM2","UNIT_MULT":"0","OBS_VALUE":"75.57"})
    wr.writerow({**base,"UNIT_MEASURE":unit2,"UNIT_MULT":multiplier2,"OBS_VALUE":"334683"})
    return out.getvalue()


def test_official_population_density_and_people_not_confused():
    a=OECDRegionalAdapter()
    try:
        rows=a.normalize_population(source_rows(),allowed_country_iso3={"AUS"})
    finally:
        a.close()
    assert len(rows)==1
    assert rows[0]["geo_code"]=="AU203"
    assert rows[0]["value"]==334683.0
    assert rows[0]["unit"]=="persons"


def test_reject_scaled_people_without_conversion():
    a=OECDRegionalAdapter()
    try:
        with pytest.raises(ValueError,match="unit multiplier"):
            a.normalize_population(source_rows(multiplier2="3"),allowed_country_iso3={"AUS"})
    finally:
        a.close()


def test_no_other_unit_can_be_mistaken_for_population():
    a=OECDRegionalAdapter()
    try:
        assert a.normalize_population(source_rows(unit2="PS_KM2"),allowed_country_iso3={"AUS"})==[]
    finally:
        a.close()
