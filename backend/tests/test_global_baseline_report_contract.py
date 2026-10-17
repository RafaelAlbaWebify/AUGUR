"""Guard the truthfulness and usefulness of full-world source acceptance reports."""
import json
from pathlib import Path
from unittest.mock import patch
from scripts import sync_global_baseline


def test_report_records_source_gaps_without_certifying_production(tmp_path, monkeypatch):
    countries=[{"iso3":"ESP"},{"iso3":"IRL"}]
    class WB:
        def __init__(self,**kwargs): pass
        def register_country_catalog(self): return countries
        def sync_countries(self, codes): return {"rows":22,"complete":True,"failures":[]}
        def close(self): pass
    class IMF:
        def __init__(self,**kwargs): pass
        def sync_countries(self,codes,*,persist=False):
            assert persist is True
            return {"rows":12,"complete":False,"failures":[{"indicator_id":"imf_unemployment_rate"}],
                    "vintage":"October 2026","source_contract":{
                    "blocked_indicator_ids":["imf_unemployment_rate"],
                    "missing_latest_actual_series":3}}
        def close(self): pass
    class UN:
        def __init__(self,**kwargs): pass
        def fetch_csv(self): return "sample"
        def sync_countries(self,codes,csv_text=None):
            return {"rows":14,"complete":False,"countries_with_data":1,"missing_country_iso3":["IRL"]}
        def close(self): pass
    monkeypatch.setattr(sync_global_baseline,"initialize_datastores",lambda:None)
    monkeypatch.setattr(sync_global_baseline,"WorldBankAdapter",WB)
    monkeypatch.setattr(sync_global_baseline,"OfficialWEOAdapter",IMF)
    monkeypatch.setattr(sync_global_baseline,"UNWPPAdapter",UN)
    monkeypatch.setattr(sync_global_baseline,"country_coverage_summary",
                        lambda:{"analyzable_country_count":2})
    output=tmp_path/"reference"/"acceptance.json"
    monkeypatch.setattr("sys.argv",["global","--imf-official-weo","--report",str(output)])
    assert sync_global_baseline.main()==0
    result=json.loads(output.read_text())
    assert result["sources"]["IMF"]["availability"]=="partial"
    assert result["sources"]["UN_WPP"]["missing_country_iso3"]==["IRL"]
    assert result["acceptance"]["source_gaps"]["imf_series_missing_actual_metadata"]==3
    assert result["acceptance"]["rankings_certified"] is False
    assert result["acceptance"]["production_database_certified"] is False
    assert result["acceptance"]["operator_production_writes"]==0
