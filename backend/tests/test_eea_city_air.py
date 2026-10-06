from app.ingestion.eea_city_air import (
    annual_record_threshold,
    select_eligible_station_means,
)


def test_annual_record_threshold_uses_75_percent_calendar_coverage():
    assert annual_record_threshold("hour", 2024) == 6588
    assert annual_record_threshold("day", 2024) == 275
    assert annual_record_threshold("hour", 2023) == 6570
    assert annual_record_threshold("day", 2023) == 274
    assert annual_record_threshold("var", 2024) is None


def test_station_selection_prefers_hourly_when_both_are_eligible():
    selected, excluded = select_eligible_station_means(
        [
            {
                "sampling_point": "A",
                "agg_type": "day",
                "record_count": 300,
                "annual_mean": 7.5,
            },
            {
                "sampling_point": "A",
                "agg_type": "hour",
                "record_count": 7000,
                "annual_mean": 7.2,
            },
            {
                "sampling_point": "B",
                "agg_type": "hour",
                "record_count": 2000,
                "annual_mean": 8.0,
            },
        ],
        2024,
    )

    assert len(selected) == 1
    assert selected[0]["sampling_point"] == "A"
    assert selected[0]["agg_type"] == "hour"
    assert any(
        item["sampling_point"] == "B"
        and item["required_records"] == 6588
        for item in excluded
    )
