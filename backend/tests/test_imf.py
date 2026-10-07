from app.ingestion.imf import IMFAdapter


def test_imf_normalization_separates_observed_and_forecast():
    payload = {
        "values": {
            "NGDP_RPCH": {
                "ESP": {
                    "2024": 3.2,
                    "2025": 2.5,
                    "2026": 2.1,
                    "2031": 1.4,
                }
            }
        }
    }

    config = {
        "indicator_id": "real_gdp_growth",
        "source_indicator": "NGDP_RPCH",
        "unit": "percent",
    }

    adapter = IMFAdapter(client=None)

    try:
        rows = adapter.normalize("ESP", config, payload)
    finally:
        adapter.close()

    assert len(rows) == 4
    assert rows[0]["source_id"] == "IMF"

    by_year = {row["period"]: row for row in rows}

    assert by_year[2025]["observation_type"] == "observed"
    assert by_year[2026]["observation_type"] == "official_forecast"
    assert by_year[2031]["observation_type"] == "official_forecast"


def test_imf_normalization_rejects_missing_spain_series():
    payload = {
        "values": {
            "NGDP_RPCH": {
                "USA": {
                    "2026": 2.0,
                }
            }
        }
    }

    config = {
        "indicator_id": "real_gdp_growth",
        "source_indicator": "NGDP_RPCH",
        "unit": "percent",
    }

    adapter = IMFAdapter(client=None)

    try:
        try:
            adapter.normalize("ESP", config, payload)
            raised = False
        except ValueError:
            raised = True
    finally:
        adapter.close()

    assert raised


def test_imf_batch_fetches_each_series_once(monkeypatch):
    from app.ingestion import imf as module

    calls = []
    stored = []

    adapter = IMFAdapter(client=None)

    payloads = {
        "NGDP_RPCH": {
            "values": {
                "NGDP_RPCH": {
                    "ESP": {"2025": 2.0, "2026": 1.8},
                    "DEU": {"2025": 1.0, "2026": 1.2},
                }
            }
        },
        "PCPIPCH": {
            "values": {
                "PCPIPCH": {
                    "ESP": {"2025": 2.5, "2026": 2.1},
                    "DEU": {"2025": 2.0, "2026": 1.9},
                }
            }
        },
        "LUR": {
            "values": {
                "LUR": {
                    "ESP": {"2025": 10.0, "2026": 9.5},
                    "DEU": {"2025": 4.0, "2026": 3.9},
                }
            }
        },
    }

    monkeypatch.setattr(
        adapter,
        "fetch_indicator",
        lambda source_indicator: (
            calls.append(source_indicator)
            or payloads[source_indicator]
        ),
    )
    monkeypatch.setattr(
        module,
        "upsert_observations",
        lambda rows: stored.extend(rows) or len(rows),
    )

    try:
        result = adapter.sync_countries(["ESP", "DEU"])
    finally:
        adapter.close()

    assert calls == ["NGDP_RPCH", "PCPIPCH", "LUR"]
    assert result["country_count"] == 2
    assert result["rows"] == 12
    assert {row["country_iso3"] for row in stored} == {"ESP", "DEU"}
