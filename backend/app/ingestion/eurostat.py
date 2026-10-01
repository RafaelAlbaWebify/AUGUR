from __future__ import annotations

import time
from datetime import datetime, timezone
from itertools import product

import httpx

from app.catalog import country_config
from app.db.analytics import upsert_observations

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
SOURCE_ID = "EUROSTAT"


EUROSTAT_SERIES = [
    {
        "indicator_id": "population_total",
        "dataset_id": "tps00001",
        "filters": {
            "geo": "__GEO__",
        },
        "unit": "persons",
    },
    {
        "indicator_id": "unemployment_rate",
        "dataset_id": "une_rt_a",
        "filters": {
            "geo": "__GEO__",
            "sex": "T",
            "age": "Y15-74",
            "unit": "PC_ACT",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "fertility_rate",
        "dataset_id": "demo_find",
        "filters": {
            "geo": "__GEO__",
            "indic_de": "TOTFERRT",
        },
        "unit": "births_per_woman",
    },
    {
        "indicator_id": "population_65_plus_share",
        "dataset_id": "demo_pjanind",
        "filters": {
            "geo": "__GEO__",
            "indic_de": "PC_Y65_MAX",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "employment_rate_20_64",
        "dataset_id": "lfsi_emp_a",
        "filters": {
            "geo": "__GEO__",
            "indic_em": "EMP_LFS",
            "sex": "T",
            "age": "Y20-64",
            "unit": "PC_POP",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "inflation_hicp",
        "dataset_id": "prc_hicp_ainr",
        "filters": {
            "geo": "__GEO__",
            "coicop18": "TOTAL",
            "unit": "RCH_A_AVG",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "public_debt_gdp",
        "dataset_id": "gov_10dd_edpt1",
        "filters": {
            "geo": "__GEO__",
            "sector": "S13",
            "unit": "PC_GDP",
            "na_item": "GD",
        },
        "unit": "percent_gdp",
    },
]


class EurostatAdapter:
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
            headers={"User-Agent": "AUGUR/0.1"},
        )
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def fetch_dataset(self, dataset_id: str, filters: dict[str, str]) -> dict:
        params = {"lang": "EN", **filters}
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(
                    f"{BASE_URL}/{dataset_id}",
                    params=params,
                )
                response.raise_for_status()
                payload = response.json()

                if not isinstance(payload, dict) or "id" not in payload or "value" not in payload:
                    raise ValueError(
                        f"Unexpected Eurostat JSON-stat response for {dataset_id}"
                    )

                return payload

            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
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

        assert last_error is not None
        raise last_error

    @staticmethod
    def _ordered_codes(dimension: dict) -> list[str]:
        index = dimension.get("category", {}).get("index", {})

        if isinstance(index, list):
            return list(index)

        if isinstance(index, dict):
            return [
                code
                for code, _position in sorted(
                    index.items(),
                    key=lambda item: item[1],
                )
            ]

        raise ValueError("Unsupported Eurostat category index")

    def normalize(self, country_iso3: str, config: dict, payload: dict) -> list[dict]:
        dimension_ids = payload["id"]
        dimension_sizes = payload["size"]
        dimensions = payload["dimension"]
        raw_values = payload["value"]

        dimension_codes = [
            self._ordered_codes(dimensions[dimension_id])
            for dimension_id in dimension_ids
        ]

        retrieved_at = datetime.now(timezone.utc)
        rows: list[dict] = []

        for coordinates in product(
            *[range(size) for size in dimension_sizes]
        ):
            flat_index = 0
            multiplier = 1

            for coordinate, size in zip(
                reversed(coordinates),
                reversed(dimension_sizes),
            ):
                flat_index += coordinate * multiplier
                multiplier *= size

            if isinstance(raw_values, list):
                value = (
                    raw_values[flat_index]
                    if flat_index < len(raw_values)
                    else None
                )
            else:
                value = raw_values.get(str(flat_index))
                if value is None:
                    value = raw_values.get(flat_index)

            if value is None:
                continue

            labels = {
                dimension_id: dimension_codes[index][coordinates[index]]
                for index, dimension_id in enumerate(dimension_ids)
            }

            time_code = labels.get("time")
            if not time_code or not str(time_code).isdigit():
                continue

            rows.append(
                {
                    "country_iso3": country_iso3.upper(),
                    "indicator_id": config["indicator_id"],
                    "period": int(time_code),
                    "value": float(value),
                    "unit": config["unit"],
                    "source_id": SOURCE_ID,
                    "dataset_id": config["dataset_id"],
                    "observation_type": "observed",
                    "retrieved_at": retrieved_at,
                    "source_updated_at": payload.get("updated"),
                    "source_observation_status": None,
                    "source_decimal": None,
                }
            )

        return rows

    def sync_country(self, country_iso3: str) -> dict:
        country = country_config(country_iso3)
        geo = country["iso2"]
        total_rows = 0
        details = []
        failures = []

        for index, config in enumerate(EUROSTAT_SERIES, start=1):
            print(
                f"[{index}/{len(EUROSTAT_SERIES)}] "
                f"{config['indicator_id']} "
                f"({config['dataset_id']})"
            )

            try:
                payload = self.fetch_dataset(
                    config["dataset_id"],
                    {key: (geo if value == "__GEO__" else value) for key, value in config["filters"].items()},
                )
                rows = self.normalize(country_iso3, config, payload)
                inserted = upsert_observations(rows)
                total_rows += inserted

                details.append(
                    {
                        "indicator_id": config["indicator_id"],
                        "dataset_id": config["dataset_id"],
                        "rows": inserted,
                        "source_updated_at": payload.get("updated"),
                    }
                )
                print(f"   ok: {inserted} rows")

            except Exception as exc:
                failures.append(
                    {
                        "indicator_id": config["indicator_id"],
                        "dataset_id": config["dataset_id"],
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                print(f"   failed: {type(exc).__name__}: {exc}")

        return {
            "country_iso3": country_iso3.upper(),
            "source": SOURCE_ID,
            "rows": total_rows,
            "series": details,
            "failures": failures,
            "complete": len(failures) == 0,
        }
