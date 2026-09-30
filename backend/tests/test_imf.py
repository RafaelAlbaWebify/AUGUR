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
        rows = adapter.normalize(config, payload)
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
            adapter.normalize(config, payload)
            raised = False
        except ValueError:
            raised = True
    finally:
        adapter.close()

    assert raised
