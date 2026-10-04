from __future__ import annotations

import time
from datetime import datetime, timezone
from itertools import product

import httpx

from app.catalog import country_config
from app.db.analytics import (
    upsert_labour_earnings,
    upsert_labour_job_transitions,
    upsert_labour_job_vacancy_rates,
    upsert_labour_net_earnings_reference,
    upsert_observations,
)

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
SOURCE_ID = "EUROSTAT"

EUROSTAT_JOB_VACANCY_RATES = {
    "dataset_id": "jvs_a_isco3_r1",
    "filters": {
        "geo": "__GEO__",
        "freq": "A",
    },
    "unit": "percent",
    "supported_iso3": {"ESP", "PRT"},
    "method": "experimental_oja_jvs_lfs_isco3_country",
}



EUROSTAT_JOB_TRANSITIONS = {
    "dataset_id": "lfsi_long_e01",
    "filters": {
        "geo": "__GEO__",
        "freq": "A",
        "unit": "PC_UNE",
        "duration": "TOTAL",
        "sex": "T",
    },
    "age_group": "Y15-74",
    "duration_group": "TOTAL",
}


EUROSTAT_NET_EARNINGS = {
    "dataset_id": "earn_nt_net",
    "filters": {
        "geo": "__GEO__",
        "freq": "A",
        "currency": "EUR",
        "estruct": "NET",
        "ecase": "P1_NCH_AW100",
    },
    "earnings_case": "P1_NCH_AW100",
    "unit": "eur_net_annual",
}


EUROSTAT_EARNINGS = {
    "dataset_id": "earn_ses22_21",
    "filters": {
        "geo": "__GEO__",
        "freq": "A",
        "unit": "EUR",
        "sizeclas": "GE10",
        "sex": "T",
        "age": "TOTAL",
        "indic_se": "ERN",
    },
    "unit": "eur_gross_monthly",
}


EUROSTAT_SERIES = [
    {
        "indicator_id": "actual_individual_consumption_index",
        "dataset_id": "prc_ppp_ind_1",
        "filters": {
            "geo": "__GEO__",
            "freq": "A",
            "indic_ppp": "VI_PPS_EU27_2020_HAB",
            "ppp_cat18": "A01",
        },
        "unit": "index_eu27_2020_100",
    },
    {
        "indicator_id": "household_internet_access",
        "dataset_id": "tin00134",
        "filters": {
            "geo": "__GEO__",
            "freq": "A",
            "unit": "PC_HH",
            "hhtyp": "TOTAL",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "intentional_homicide_rate",
        "dataset_id": "crim_off_cat",
        "filters": {
            "geo": "__GEO__",
            "freq": "A",
            "iccs": "ICCS0101",
            "unit": "P_HTHAB",
        },
        "unit": "per_100k_people",
    },
    {
        "indicator_id": "pm25_premature_death_rate",
        "dataset_id": "sdg_11_52",
        "filters": {
            "geo": "__GEO__",
            "freq": "A",
        },
        "label_contains": {
            "unit": "Rate",
        },
        "unit": "per_100k_people",
    },
    {
        "indicator_id": "real_house_price_index",
        "dataset_id": "tipsho10",
        "filters": {
            "geo": "__GEO__",
            "freq": "A",
            "unit": "I15_A_AVG",
        },
        "unit": "index_2015_100",
    },
    {
        "indicator_id": "rent_price_index",
        "dataset_id": "prc_hicp_aind",
        "filters": {
            "geo": "__GEO__",
            "freq": "A",
            "unit": "INX_A_AVG",
            "coicop": "CP041",
        },
        "unit": "index_annual_average",
    },
    {
        "indicator_id": "household_price_level_index",
        "dataset_id": "prc_ppp_ind",
        "filters": {
            "geo": "__GEO__",
            "freq": "A",
            "na_item": "PLI_EU27_2020",
            "ppp_cat": "E011",
        },
        "unit": "index_eu27_2020_100",
    },
    {
        "indicator_id": "housing_cost_overburden_rate",
        "dataset_id": "tessi163",
        "filters": {
            "geo": "__GEO__",
            "freq": "A",
            "unit": "PC",
            "rskpovth": "TOTAL",
            "age": "TOTAL",
            "sex": "T",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "tertiary_education_25_34",
        "dataset_id": "sdg_04_20",
        "filters": {
            "geo": "__GEO__",
            "freq": "A",
            "unit": "PC",
            "age": "Y25-34",
            "isced11": "ED5-8",
            "sex": "T",
        },
        "unit": "percent",
    },
    {
        "indicator_id": "energy_import_dependency",
        "dataset_id": "nrg_ind_id",
        "filters": {
            "geo": "__GEO__",
            "freq": "A",
            "unit": "PC",
            "siec": "TOTAL",
        },
        "unit": "percent",
    },
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

    @staticmethod
    def _category_labels(dimension: dict) -> dict[str, str]:
        labels = dimension.get("category", {}).get("label", {})
        return labels if isinstance(labels, dict) else {}

    def _labels_match_config(
        self,
        config: dict,
        labels: dict[str, str],
        dimensions: dict,
    ) -> bool:
        requirements = config.get("label_contains") or {}
        for dimension_id, required_text in requirements.items():
            code = labels.get(dimension_id)
            if code is None:
                return False
            human_label = self._category_labels(
                dimensions.get(dimension_id, {})
            ).get(code, code)
            if required_text.casefold() not in str(human_label).casefold():
                return False
        return True

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

            if not self._labels_match_config(config, labels, dimensions):
                continue

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

    def normalize_earnings(
        self,
        country_iso3: str,
        payload: dict,
    ) -> list[dict]:
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
            isco08 = labels.get("isco08")

            if (
                not time_code
                or not str(time_code).isdigit()
                or not isco08
                or isco08 == "TOTAL"
            ):
                continue

            rows.append(
                {
                    "country_iso3": country_iso3.upper(),
                    "period": int(time_code),
                    "isco08": str(isco08),
                    "value": float(value),
                    "unit": EUROSTAT_EARNINGS["unit"],
                    "source_id": SOURCE_ID,
                    "dataset_id": EUROSTAT_EARNINGS["dataset_id"],
                    "retrieved_at": retrieved_at,
                    "source_updated_at": payload.get("updated"),
                }
            )

        return rows

    def normalize_net_earnings(
        self,
        country_iso3: str,
        payload: dict,
    ) -> list[dict]:
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
            earnings_case = labels.get("ecase") or EUROSTAT_NET_EARNINGS["earnings_case"]

            if not time_code or not str(time_code).isdigit():
                continue

            rows.append(
                {
                    "country_iso3": country_iso3.upper(),
                    "period": int(time_code),
                    "earnings_case": str(earnings_case),
                    "annual_net_eur": float(value),
                    "source_id": SOURCE_ID,
                    "dataset_id": EUROSTAT_NET_EARNINGS["dataset_id"],
                    "retrieved_at": retrieved_at,
                    "source_updated_at": payload.get("updated"),
                }
            )

        return rows

    def normalize_job_vacancy_rates(
        self,
        country_iso3: str,
        payload: dict,
    ) -> list[dict]:
        dimension_ids = payload["id"]
        dimension_sizes = payload["size"]
        dimensions = payload["dimension"]
        raw_values = payload["value"]

        dimension_codes = [
            self._ordered_codes(dimensions[dimension_id])
            for dimension_id in dimension_ids
        ]

        isco_dimension_id = next(
            (
                dimension_id
                for dimension_id in dimension_ids
                if "isco" in str(dimension_id).lower()
            ),
            None,
        )
        if isco_dimension_id is None:
            isco_dimension_id = next(
                (
                    dimension_id
                    for dimension_id in dimension_ids
                    if "occupation" in str(
                        dimensions.get(dimension_id, {}).get("label", "")
                    ).lower()
                    or "international standard classification of occupations" in str(
                        dimensions.get(dimension_id, {}).get("label", "")
                    ).lower()
                ),
                None,
            )
        if isco_dimension_id is None:
            raise ValueError(
                "Eurostat experimental vacancy payload has no ISCO dimension; "
                f"received dimensions={dimension_ids}"
            )

        indicator_dimension_id = next(
            (
                dimension_id
                for dimension_id in dimension_ids
                if str(dimension_id).lower() == "indic_em"
            ),
            None,
        )

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

            period = labels.get("time")
            isco08 = str(labels.get(isco_dimension_id) or "")
            employment_indicator = (
                str(labels.get(indicator_dimension_id) or "")
                if indicator_dimension_id
                else "JVR"
            )

            if not period:
                continue
            if indicator_dimension_id and employment_indicator != "JVR":
                continue
            if (
                len(isco08) != 5
                or not isco08.startswith("OC")
                or not isco08[2:].isdigit()
            ):
                continue

            rows.append(
                {
                    "country_iso3": country_iso3.upper(),
                    "period": str(period),
                    "isco08": isco08,
                    "vacancy_rate_pct": float(value),
                    "nace_scope": None,
                    "source_id": SOURCE_ID,
                    "dataset_id": EUROSTAT_JOB_VACANCY_RATES["dataset_id"],
                    "retrieved_at": retrieved_at,
                    "source_updated_at": payload.get("updated"),
                }
            )

        if not rows:
            isco_codes = self._ordered_codes(dimensions[isco_dimension_id])[:20]
            indicator_codes = (
                self._ordered_codes(dimensions[indicator_dimension_id])[:20]
                if indicator_dimension_id
                else []
            )
            raise ValueError(
                "Eurostat experimental vacancy payload produced no ISCO-3 JVR rows; "
                f"dimensions={dimension_ids}; "
                f"isco_dimension={isco_dimension_id}; "
                f"isco_codes={isco_codes}; "
                f"indicator_dimension={indicator_dimension_id}; "
                f"indicator_codes={indicator_codes}"
            )

        return rows

    def normalize_job_transitions(
        self,
        country_iso3: str,
        payload: dict,
    ) -> list[dict]:
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
            age_group = labels.get("age") or labels.get("AGE")
            duration_group = labels.get("duration")

            if not time_code or not str(time_code).isdigit():
                continue

            rows.append(
                {
                    "country_iso3": country_iso3.upper(),
                    "period": int(time_code),
                    "age_group": (
                        str(age_group)
                        if age_group
                        else EUROSTAT_JOB_TRANSITIONS["age_group"]
                    ),
                    "duration_group": (
                        str(duration_group)
                        if duration_group
                        else EUROSTAT_JOB_TRANSITIONS["duration_group"]
                    ),
                    "probability_pct": float(value),
                    "source_id": SOURCE_ID,
                    "dataset_id": EUROSTAT_JOB_TRANSITIONS["dataset_id"],
                    "retrieved_at": retrieved_at,
                    "source_updated_at": payload.get("updated"),
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
                if not rows:
                    raise ValueError(
                        "Eurostat returned no observations matching the configured filters"
                    )
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

        earnings_detail = None
        try:
            print(
                f"[earnings] mean monthly earnings by ISCO "
                f"({EUROSTAT_EARNINGS['dataset_id']})"
            )
            payload = self.fetch_dataset(
                EUROSTAT_EARNINGS["dataset_id"],
                {
                    key: (geo if value == "__GEO__" else value)
                    for key, value in EUROSTAT_EARNINGS["filters"].items()
                },
            )
            earnings_rows = self.normalize_earnings(country_iso3, payload)
            inserted = upsert_labour_earnings(earnings_rows)
            total_rows += inserted
            earnings_detail = {
                "dataset_id": EUROSTAT_EARNINGS["dataset_id"],
                "rows": inserted,
                "source_updated_at": payload.get("updated"),
            }
            print(f"   ok: {inserted} earnings rows")
        except Exception as exc:
            failures.append(
                {
                    "indicator_id": "labour_earnings_by_isco",
                    "dataset_id": EUROSTAT_EARNINGS["dataset_id"],
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            print(f"   failed: {type(exc).__name__}: {exc}")

        net_earnings_detail = None
        try:
            print(
                f"[net-earnings] annual net earnings benchmark "
                f"({EUROSTAT_NET_EARNINGS['dataset_id']})"
            )
            payload = self.fetch_dataset(
                EUROSTAT_NET_EARNINGS["dataset_id"],
                {
                    key: (geo if value == "__GEO__" else value)
                    for key, value in EUROSTAT_NET_EARNINGS["filters"].items()
                },
            )
            net_rows = self.normalize_net_earnings(
                country_iso3,
                payload,
            )
            inserted = upsert_labour_net_earnings_reference(net_rows)
            total_rows += inserted
            net_earnings_detail = {
                "dataset_id": EUROSTAT_NET_EARNINGS["dataset_id"],
                "rows": inserted,
                "source_updated_at": payload.get("updated"),
            }
            print(f"   ok: {inserted} net-earnings rows")
        except Exception as exc:
            failures.append(
                {
                    "indicator_id": "annual_net_earnings_reference",
                    "dataset_id": EUROSTAT_NET_EARNINGS["dataset_id"],
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            print(f"   failed: {type(exc).__name__}: {exc}")

        job_vacancy_detail = None
        if country_iso3.upper() not in EUROSTAT_JOB_VACANCY_RATES["supported_iso3"]:
            job_vacancy_detail = {
                "dataset_id": EUROSTAT_JOB_VACANCY_RATES["dataset_id"],
                "rows": 0,
                "status": "source_coverage_unavailable",
                "method": EUROSTAT_JOB_VACANCY_RATES["method"],
            }
            print(
                "[job-vacancy] source coverage unavailable for "
                f"{country_iso3.upper()} in "
                f"{EUROSTAT_JOB_VACANCY_RATES['dataset_id']}"
            )
        else:
            try:
                print(
                    f"[job-vacancy] vacancy rate by ISCO 3-digit occupation "
                    f"({EUROSTAT_JOB_VACANCY_RATES['dataset_id']})"
                )
                payload = self.fetch_dataset(
                    EUROSTAT_JOB_VACANCY_RATES["dataset_id"],
                    {
                        key: (geo if value == "__GEO__" else value)
                        for key, value in EUROSTAT_JOB_VACANCY_RATES["filters"].items()
                    },
                )
                vacancy_rows = self.normalize_job_vacancy_rates(
                    country_iso3,
                    payload,
                )
                inserted = upsert_labour_job_vacancy_rates(vacancy_rows)
                total_rows += inserted
                job_vacancy_detail = {
                    "dataset_id": EUROSTAT_JOB_VACANCY_RATES["dataset_id"],
                    "rows": inserted,
                    "source_updated_at": payload.get("updated"),
                    "status": "available",
                    "method": EUROSTAT_JOB_VACANCY_RATES["method"],
                }
                print(f"   ok: {inserted} vacancy-rate rows")
            except Exception as exc:
                failures.append(
                    {
                        "indicator_id": "job_vacancy_rate_by_isco",
                        "dataset_id": EUROSTAT_JOB_VACANCY_RATES["dataset_id"],
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                print(f"   failed: {type(exc).__name__}: {exc}")

        job_transition_detail = None
        try:
            print(
                f"[job-transition] unemployment to employment probability "
                f"({EUROSTAT_JOB_TRANSITIONS['dataset_id']})"
            )
            payload = self.fetch_dataset(
                EUROSTAT_JOB_TRANSITIONS["dataset_id"],
                {
                    key: (geo if value == "__GEO__" else value)
                    for key, value in EUROSTAT_JOB_TRANSITIONS["filters"].items()
                },
            )
            transition_rows = self.normalize_job_transitions(
                country_iso3,
                payload,
            )
            inserted = upsert_labour_job_transitions(transition_rows)
            total_rows += inserted
            job_transition_detail = {
                "dataset_id": EUROSTAT_JOB_TRANSITIONS["dataset_id"],
                "rows": inserted,
                "source_updated_at": payload.get("updated"),
            }
            print(f"   ok: {inserted} transition rows")
        except Exception as exc:
            failures.append(
                {
                    "indicator_id": "unemployment_to_employment_probability",
                    "dataset_id": EUROSTAT_JOB_TRANSITIONS["dataset_id"],
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
            "earnings": earnings_detail,
            "net_earnings": net_earnings_detail,
            "job_vacancy": job_vacancy_detail,
            "job_transition": job_transition_detail,
            "failures": failures,
            "complete": len(failures) == 0,
        }
