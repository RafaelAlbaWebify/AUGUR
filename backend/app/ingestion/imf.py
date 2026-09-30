from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx

from app.db.analytics import upsert_observations

BASE_URL = "https://www.imf.org/external/datamapper/api/v2"
SOURCE_ID = "IMF"
DATASET_ID = "WEO_APRIL_2026"
FORECAST_START_YEAR = 2026

SERIES = [
    {
        "indicator_id": "real_gdp_growth",
        "source_indicator": "NGDP_RPCH",
        "unit": "percent",
    },
    {
        "indicator_id": "imf_inflation_average",
        "source_indicator": "PCPIPCH",
        "unit": "percent",
    },
    {
        "indicator_id": "imf_unemployment_rate",
        "source_indicator": "LUR",
        "unit": "percent",
    },
]


class IMFAdapter:
    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout_seconds: float = 90.0,
        max_retries: int = 3,
    ):
        self.max_retries = max_retries
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 AUGUR/0.1",
                "Accept": "application/json",
            },
        )
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def fetch_indicator(self, source_indicator: str) -> dict:
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(
                    f"{BASE_URL}/{source_indicator}",
                )
                response.raise_for_status()
                payload = response.json()

                values = payload.get("values")
                if not isinstance(values, dict):
                    raise ValueError(
                        f"Unexpected IMF response for {source_indicator}: missing values"
                    )

                return payload

            except (
                httpx.TimeoutException,
                httpx.TransportError,
                httpx.HTTPStatusError,
            ) as exc:
                last_error = exc

                if attempt >= self.max_retries:
                    break

                delay_seconds = 2 ** (attempt - 1)
                print(
                    f"   retry {attempt}/{self.max_retries - 1} "
                    f"after {type(exc).__name__} "
                    f"(waiting {delay_seconds}s)"
                )
                time.sleep(delay_seconds)

        if last_error is not None:
            raise last_error

        raise RuntimeError("IMF request failed without an exception")

    def normalize(self, config: dict, payload: dict) -> list[dict]:
        source_indicator = config["source_indicator"]
        values = payload.get("values", {})
        indicator_values = values.get(source_indicator, {})
        country_values = indicator_values.get("ESP", {})

        if not isinstance(country_values, dict):
            raise ValueError(
                f"IMF response for {source_indicator} has no ESP series"
            )

        retrieved_at = datetime.now(timezone.utc)
        rows: list[dict] = []

        for year_text, raw_value in country_values.items():
            if not str(year_text).isdigit() or raw_value is None:
                continue

            year = int(year_text)

            rows.append(
                {
                    "country_iso3": "ESP",
                    "indicator_id": config["indicator_id"],
                    "period": year,
                    "value": float(raw_value),
                    "unit": config["unit"],
                    "source_id": SOURCE_ID,
                    "dataset_id": DATASET_ID,
                    "observation_type": (
                        "official_forecast"
                        if year >= FORECAST_START_YEAR
                        else "observed"
                    ),
                    "retrieved_at": retrieved_at,
                    "source_updated_at": "2026-04",
                    "source_observation_status": None,
                    "source_decimal": None,
                }
            )

        if not rows:
            raise ValueError(
                f"IMF response for {source_indicator} contained no usable ESP observations"
            )

        return rows

    def sync_spain(self) -> dict:
        total_rows = 0
        details = []
        failures = []

        for index, config in enumerate(SERIES, start=1):
            print(
                f"[{index}/{len(SERIES)}] "
                f"{config['indicator_id']} "
                f"({config['source_indicator']})"
            )

            try:
                payload = self.fetch_indicator(config["source_indicator"])
                rows = self.normalize(config, payload)
                inserted = upsert_observations(rows)
                total_rows += inserted

                observed = sum(
                    row["observation_type"] == "observed" for row in rows
                )
                forecasts = sum(
                    row["observation_type"] == "official_forecast" for row in rows
                )

                details.append(
                    {
                        "indicator_id": config["indicator_id"],
                        "source_indicator": config["source_indicator"],
                        "rows": inserted,
                        "observed": observed,
                        "official_forecasts": forecasts,
                    }
                )
                print(
                    f"   ok: {inserted} rows "
                    f"({observed} observed, {forecasts} forecasts)"
                )

            except Exception as exc:
                failures.append(
                    {
                        "indicator_id": config["indicator_id"],
                        "source_indicator": config["source_indicator"],
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                print(f"   failed: {type(exc).__name__}: {exc}")

        return {
            "country_iso3": "ESP",
            "source": SOURCE_ID,
            "vintage": "April 2026",
            "rows": total_rows,
            "series": details,
            "failures": failures,
            "complete": len(failures) == 0,
        }
