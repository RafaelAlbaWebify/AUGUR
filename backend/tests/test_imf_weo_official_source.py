"""October WEO source contract: no guessed historical/forecast boundary."""
from io import BytesIO
from openpyxl import Workbook
import pytest
from app.ingestion.imf_weo_official import normalize_official_weo,DATASET_VERSION
from scripts.verify_weo_disposable_readthrough import verify_weo_roundtrip


def workbook(*,unit="Percent",actual=2024,bad=False):
    book=Workbook()
    sheet=book.active
    sheet.title="Countries"
    sheet.append(["DATASET","COUNTRY.ID","INDICATOR.ID","FREQUENCY","UNIT",
                  "LATEST_ACTUAL_ANNUAL_DATA","PUBLICATION_DATE","2024","2025","2026"])
    for code,series,cutoff,u in [
        ("ESP","NGDP_RPCH",actual,unit),
        ("ESP","PCPIPCH",2025,"Percent"),
        ("ESP","LUR",2025,None),
    ]:
        sheet.append([DATASET_VERSION,code,series,"Annual",u,cutoff,"2026-10-13T02:00:00Z",
                      2.0,3.0,"invalid" if bad and series=="NGDP_RPCH" else 4.0])
    mem=BytesIO();book.save(mem);book.close()
    return mem.getvalue()


def test_uses_actual_annual_metadata_not_universal_calendar_boundary():
    rows,report=normalize_official_weo(workbook(),{"ESP"})
    assert len(rows)==6
    by_metric={(r["indicator_id"],r["period"]):r["observation_type"] for r in rows}
    assert by_metric[("real_gdp_growth",2025)]=="official_forecast"
    assert by_metric[("imf_inflation_average",2025)]=="observed"
    assert report["blocked_indicator_ids"]==["imf_unemployment_rate"]
    assert report["production_writes"]==0


def test_untrusted_source_unit_is_rejected():
    with pytest.raises(ValueError,match="Unsupported IMF unit"):
        normalize_official_weo(workbook(unit="Index"),{"ESP"})


def test_nonnumeric_source_values_are_rejected():
    with pytest.raises(ValueError,match="Invalid IMF WEO value"):
        normalize_official_weo(workbook(bad=True),{"ESP"})


def test_missing_latest_actual_cannot_be_guessed():
    rows,report=normalize_official_weo(workbook(actual=None),{"ESP"})
    assert len(rows)==3
    assert report["missing_latest_actual_series"]==1


def test_missing_country_is_not_imputed():
    rows,report=normalize_official_weo(workbook(),{"IRL"})
    assert rows==[]
    assert report["countries_with_data"]==[]


def test_official_weo_parser_roundtrips_through_real_disposable_duckdb():
    rows,_=normalize_official_weo(workbook(),{"ESP"})
    result=verify_weo_roundtrip(rows)
    assert result["expected_rows"]==result["stored_rows"]==6
    assert result["production_writes"]==0
    assert result["ranking_eligible"] is False
