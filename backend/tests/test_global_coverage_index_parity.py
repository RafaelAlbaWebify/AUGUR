"""Indexed coverage must preserve statuses, periods and rejected reasons."""
from app.services.global_evidence_contract import EvidenceContract,coverage_matrix

C=EvidenceContract("gdp","usd",("country","region"),"WB","series-v1")
GEOS=[{"country_iso3":"ESP","geo_level":"country","geo_code":"ESP","geography_system":"ISO"},
      {"country_iso3":"PRT","geo_level":"country","geo_code":"PRT","geography_system":"ISO"},
      {"country_iso3":"ESP","geo_level":"region","geo_code":"ES11","geography_system":"NUTS"}]
ROWS=[{"indicator_id":"gdp","unit":"usd","source_id":"WB","dataset_id":"series-v1",
       "geo_code":"ESP","geo_level":"country","geography_system":"ISO","period":2025,"value":3.0},
      {"indicator_id":"gdp","unit":"bad","source_id":"WB","dataset_id":"series-v1",
       "geo_code":"ESP","geo_level":"country","geography_system":"ISO","period":2024,"value":3.5},
      {"indicator_id":"gdp","unit":"bad","source_id":"WB","dataset_id":"series-v1",
       "geo_code":"ES11","geo_level":"region","geography_system":"NUTS","period":2025,"value":3.0}]

def test_indexed_coverage_distinguishes_observed_missing_and_incompatible():
    result=coverage_matrix([C],ROWS,GEOS)
    assert [r["status"] for r in result]==["observed","missing","incompatible"]
    assert result[0]["periods"]==[2025]
    assert result[0]["rejected_reasons"]==["unit_mismatch"]
    assert result[1]["periods"]==[]
    assert result[2]["rejected_reasons"]==["unit_mismatch"]

def test_duplicate_observed_rows_and_geo_system_remain_separate():
    duplicates=ROWS+[dict(ROWS[0],period=2023)]
    result=coverage_matrix([C],duplicates,GEOS)
    assert result[0]["periods"]==[2023,2025]
    assert result[2]["status"]=="incompatible"
    assert len(result)==3

def test_empty_observations_preserve_missing_values():
    assert all(r["status"]=="missing" for r in coverage_matrix([C],[],GEOS))
