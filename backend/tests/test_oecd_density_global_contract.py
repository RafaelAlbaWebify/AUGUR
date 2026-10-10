import pytest
from app.ingestion import oecd_regional as module
from app.ingestion.oecd_regional import OECDRegionalAdapter

CSV = """TERRITORIAL_LEVEL,REF_AREA,Reference area,UNIT_MEASURE,TIME_PERIOD,OBS_VALUE,COUNTRY
TL2,AU1,New South Wales,PS_KM2,2024,10.58,AUS
"""

def test_non_eu_oecd_density_sync_accepts_matching_contract(monkeypatch):
    stored=[]
    monkeypatch.setattr(module, "upsert_subnational_observations", lambda rows: stored.extend(rows) or len(rows))
    adapter=OECDRegionalAdapter()
    monkeypatch.setattr(adapter, "fetch_density", lambda **kwargs: CSV)
    try:
        result=adapter.sync_density(allowed_country_iso3={"AUS"})
    finally:
        adapter.close()
    assert result["rows"] == 1
    assert stored[0]["country_iso3"] == "AUS"
    assert stored[0]["geography_system"] == "OECD_TL_2024"

def test_oecd_density_rejects_invalid_geography_before_write(monkeypatch):
    monkeypatch.setattr(module, "upsert_subnational_observations", lambda rows: pytest.fail("bad row was stored"))
    adapter=OECDRegionalAdapter()
    monkeypatch.setattr(adapter, "fetch_density", lambda **kwargs: CSV)
    original=adapter.normalize_density
    def invalid(*args, **kwargs):
        rows=original(*args, **kwargs)
        rows[0]["geography_system"]="NUTS_2024"
        return rows
    monkeypatch.setattr(adapter, "normalize_density", invalid)
    try:
        with pytest.raises(ValueError, match="geography_system_mismatch"):
            adapter.sync_density(allowed_country_iso3={"AUS"})
    finally:
        adapter.close()
