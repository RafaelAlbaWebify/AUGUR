from app.services.geography_indicator_coverage import coverage_band


def test_coverage_bands():
    assert coverage_band(1.0) == "strong"
    assert coverage_band(0.90) == "strong"
    assert coverage_band(0.899) == "partial"
    assert coverage_band(0.50) == "partial"
    assert coverage_band(0.499) == "sparse"
    assert coverage_band(0.01) == "sparse"
    assert coverage_band(0) == "absent"
