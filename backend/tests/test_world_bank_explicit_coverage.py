"""Source reachability is not equivalent to statistical country coverage."""
from app.ingestion import world_bank as module


def test_world_bank_partial_country_observations_not_complete(monkeypatch):
    class Fake(module.WorldBankAdapter):
        def fetch_indicator_many(self,*args,**kwargs):
            return {"lastupdated":"2026-10-01"}, [
                {"countryiso3code":"ESP","date":"2025","value":20,
                 "country":{"id":"ESP"}}]
    monkeypatch.setattr(module,"world_bank_indicators",lambda:[{
        "indicator_id":"population_total","source_indicator":"SP.POP.TOTL","unit":"persons"}])
    monkeypatch.setattr(module,"upsert_observations",lambda rows:len(rows))
    adapter=Fake()
    try: report=adapter.sync_countries(["ESP","IRL"])
    finally: adapter.close()
    assert report["rows"]==1
    assert report["complete"] is False
    assert report["indicators"][0]["countries_with_data"]==1
    assert report["indicators"][0]["missing_country_iso3"]==["IRL"]


def test_world_bank_empty_success_response_cannot_be_complete(monkeypatch):
    class Fake(module.WorldBankAdapter):
        def fetch_indicator_many(self,*args,**kwargs): return {},[]
    monkeypatch.setattr(module,"world_bank_indicators",lambda:[{
        "indicator_id":"population_total","source_indicator":"SP.POP.TOTL","unit":"persons"}])
    monkeypatch.setattr(module,"upsert_observations",lambda rows:len(rows))
    adapter=Fake()
    try: report=adapter.sync_countries(["ESP"])
    finally: adapter.close()
    assert report["complete"] is False
    assert report["indicators"][0]["missing_country_iso3"]==["ESP"]
