"""Benchmark invariants and invalid workload rejection."""
import pytest
from scripts.benchmark_compare import benchmark, fixture


def test_two_country_fixture_has_unique_29_indicator_records():
    snapshots=fixture()
    assert len(snapshots["ESP"]) == len(snapshots["IRL"]) == 29
    assert len({entry["indicator_id"] for entry in snapshots["ESP"]}) == 29


def test_benchmark_reports_reproducible_units_without_claiming_speedup():
    result=benchmark(iterations=4,indicators=3)
    assert result["countries"] == 2
    assert result["indicators"] == 3
    assert result["iterations"] == 4
    assert result["median_ms"] >= 0
    assert result["p95_ms"] >= 0
    assert result["tracemalloc_peak_bytes"] > 0


@pytest.mark.parametrize("iterations, indicators", [(0,29), (1,0), (-1,29)])
def test_invalid_benchmark_workload_fails(iterations, indicators):
    with pytest.raises(ValueError):
        benchmark(iterations=iterations,indicators=indicators)
