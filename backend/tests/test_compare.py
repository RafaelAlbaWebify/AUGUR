from app.services.compare import build_comparison


def test_build_comparison_aligns_country_values():
    snapshots = {
        "ESP": [
            {
                "indicator_id": "unemployment_rate",
                "name": "Unemployment",
                "dimension": "productive_capacity",
                "unit": "percent",
                "period": 2025,
                "value": 10.4,
                "source_id": "EUROSTAT",
            }
        ],
        "PRT": [
            {
                "indicator_id": "unemployment_rate",
                "name": "Unemployment",
                "dimension": "productive_capacity",
                "unit": "percent",
                "period": 2025,
                "value": 6.4,
                "source_id": "EUROSTAT",
            }
        ],
    }

    result = build_comparison(["ESP", "PRT"], snapshots)

    assert result["indicator_count"] == 1
    row = result["indicators"][0]
    assert row["countries"]["ESP"]["value"] == 10.4
    assert row["countries"]["PRT"]["value"] == 6.4
    assert result["method"] == "aligned_current_observations_v1"
