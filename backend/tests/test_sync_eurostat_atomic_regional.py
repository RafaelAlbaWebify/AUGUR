"""Eurostat orchestrator cannot partially persist regional source batches."""
import sys
from datetime import datetime, timezone
import pytest
from scripts import sync_eurostat


class Adapter:
    def __init__(self, *args, **kwargs):
        pass
    def sync_country(self, country):
        return {"complete": True, "rows": 0, "series": [], "failures": []}
    def close(self):
        pass


def labour_row(value=70.0):
    return {"geo_code": "ES11", "geo_level": "NUTS2",
            "indicator_id": "regional_employment_rate",
            "period": 2025, "value": value, "unit": "percent",
            "source_id": "EUROSTAT", "dataset_id": "lfst_r_lfe2emprt",
            "retrieved_at": datetime.now(timezone.utc)}


def arrange(monkeypatch, labour, housing=None, health=None, sector=None):
    calls=[]
    monkeypatch.setattr(sync_eurostat, "initialize_datastores", lambda: None)
    monkeypatch.setattr(sync_eurostat, "EurostatAdapter", Adapter)
    monkeypatch.setattr(sync_eurostat, "fetch_regional_labour", lambda adapter: (labour, []))
    monkeypatch.setattr(sync_eurostat, "fetch_regional_housing_evidence", lambda adapter: (housing or [], []))
    monkeypatch.setattr(sync_eurostat, "fetch_regional_health_evidence", lambda adapter: (health or [], []))
    monkeypatch.setattr(sync_eurostat, "fetch_regional_sector_employment", lambda adapter: (sector or [], []))
    monkeypatch.setattr(sync_eurostat, "upsert_subnational_observations",
                        lambda rows: calls.append(("regional", len(rows))) or len(rows))
    monkeypatch.setattr(sync_eurostat, "upsert_regional_sector_employment",
                        lambda rows: calls.append(("sector", len(rows))) or len(rows))
    monkeypatch.setattr(sys, "argv", ["sync_eurostat", "--countries", "ESP"])
    return calls


def test_invalid_region_prevents_all_regional_writes(monkeypatch):
    calls=arrange(monkeypatch, [labour_row(value=float("nan"))])
    with pytest.raises(ValueError, match="contract failed"):
        sync_eurostat.main()
    assert calls==[]


def test_duplicate_across_regional_batches_fails_before_writes(monkeypatch):
    calls=arrange(monkeypatch, [labour_row()], health=[dict(labour_row())])
    with pytest.raises(ValueError, match="Duplicate observation write key"):
        sync_eurostat.main()
    assert calls==[]


def test_combined_regional_batch_written_once(monkeypatch):
    calls=arrange(monkeypatch, [labour_row()])
    assert sync_eurostat.main()==0
    assert calls==[("regional", 1), ("sector", 0)]
