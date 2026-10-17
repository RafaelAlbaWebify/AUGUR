"""Explicit global provider coverage: missing countries are not zero."""
from unittest.mock import patch
from app.ingestion.un_wpp import UNWPPAdapter


def test_missing_wpp_country_codes_remain_visible():
    adapter=UNWPPAdapter()
    rows=[{"country_iso3":"ESP","observation_type":"observed","indicator_id":"population_total"}]
    try:
        with patch.object(adapter,"normalize_countries",return_value=rows), patch("app.ingestion.un_wpp.upsert_observations",return_value=1):
            result=adapter.sync_countries(["ESP","IRL"],csv_text="dummy")
    finally:
        adapter.close()
    assert result["countries_with_data"]==1
    assert result["missing_country_iso3"]==["IRL"]
    assert result["complete"] is False
