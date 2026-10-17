"""Regress IMF complete=false when providers block all requested series."""
from unittest.mock import patch
from app.ingestion.imf import IMFAdapter, SERIES


def test_all_blocked_imf_series_are_not_complete():
    adapter = IMFAdapter()
    try:
        with patch.object(adapter, "fetch_indicator", side_effect=PermissionError("HTTP 403")):
            result = adapter.sync_countries(["ESP", "IRL"])
    finally:
        adapter.close()
    assert result["rows"] == 0
    assert result["series"] == []
    assert len(result["failures"]) == len(SERIES)
    assert result["complete"] is False
