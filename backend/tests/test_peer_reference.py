from app.services.peer_reference import build_peer_reference


def test_peer_reference_uses_latest_common_period():
    series = {
        "ESP": [
            {"period": 2024, "value": 10.0},
            {"period": 2025, "value": 9.0},
        ],
        "PRT": [
            {"period": 2024, "value": 6.0},
            {"period": 2025, "value": 5.0},
        ],
        "IRL": [
            {"period": 2024, "value": 4.0},
        ],
    }

    result = build_peer_reference("unemployment_rate", "ESP", series)

    assert result["status"] == "available"
    assert result["period"] == 2024
    assert result["sample_size"] == 3
    assert result["rank_low_to_high"] == 3.0
    assert result["percentile_low_to_high"] == 100.0
    assert result["adequacy"] == "limited"


def test_peer_reference_handles_ties_with_average_rank():
    series = {
        "ESP": [{"period": 2025, "value": 5.0}],
        "PRT": [{"period": 2025, "value": 5.0}],
        "IRL": [{"period": 2025, "value": 8.0}],
    }

    result = build_peer_reference("example", "ESP", series)

    assert result["rank_low_to_high"] == 1.5
    assert result["percentile_low_to_high"] == 25.0


def test_peer_reference_requires_common_period():
    series = {
        "ESP": [{"period": 2025, "value": 5.0}],
        "PRT": [{"period": 2024, "value": 5.0}],
        "IRL": [{"period": 2023, "value": 8.0}],
    }

    result = build_peer_reference("example", "ESP", series)

    assert result["status"] == "insufficient_common_period"
    assert result["adequacy"] == "insufficient"
