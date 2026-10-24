"""Reproducible, disposable benchmark of AUGUR two-country comparison.

Run from backend: python -m scripts.benchmark_compare --iterations 500
Uses synthetic 29-indicator workloads; does not open any operator database.
Reports measurements, not speedups; machine differences preclude absolute CI caps.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc

from app.services.compare import build_comparison


def fixture(count: int = 29) -> dict[str, list[dict]]:
    if count < 1:
        raise ValueError("At least one indicator is required")
    result = {}
    for country, shift in (("ESP", 0.0), ("IRL", 2.0)):
        result[country] = [
            {"indicator_id": f"test_indicator_{index}", "name": f"Test indicator {index}",
             "dimension": "prosperity", "unit": "percent", "period": 2025,
             "value": float(index) + shift, "source_id": "SYNTHETIC"}
            for index in range(count)
        ]
    return result


def benchmark(iterations: int = 500, indicators: int = 29) -> dict:
    if iterations <= 0:
        raise ValueError("Iterations must be positive")
    snapshots = fixture(indicators)
    for _ in range(10):
        build_comparison(["ESP", "IRL"], snapshots)
    timings = []
    tracemalloc.start()
    try:
        for _ in range(iterations):
            start = time.perf_counter_ns()
            result = build_comparison(["ESP", "IRL"], snapshots)
            timings.append((time.perf_counter_ns() - start) / 1_000_000)
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    if result["indicator_count"] != indicators:
        raise AssertionError("Benchmark output changed: indicator count mismatch")
    ordered = sorted(timings)
    return {"workload": "synthetic_2_country_comparison",
            "countries": 2, "indicators": indicators, "iterations": iterations,
            "median_ms": round(statistics.median(timings), 5),
            "p95_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * .95))], 5),
            "tracemalloc_peak_bytes": peak_bytes,
            "notes": "Synthetic in-memory comparison only; excludes DuckDB, HTTP, frontend rendering, startup and CPU/I/O profiling"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--indicators", type=int, default=29)
    options = parser.parse_args()
    print(json.dumps(benchmark(options.iterations, options.indicators), indent=2))


if __name__ == "__main__":
    main()
