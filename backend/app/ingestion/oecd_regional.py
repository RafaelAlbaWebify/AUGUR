from __future__ import annotations

import csv
import io
import time
from datetime import datetime, timezone

import httpx

from app.db.analytics import upsert_subnational_observations


SOURCE_ID = "OECD"
DATASET_ID = "DSD_REG_DEMO@DF_DENSITY"
DATASET_VERSION = "2.4"
GEOGRAPHY_SYSTEM = "OECD_TL_2024"
DENSITY_BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_DEMO@DF_DENSITY,2.4"
)
POPULATION_DATASET_ID = "DSD_REG_DEMO@DF_POP_BROAD"
POPULATION_BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_DEMO@DF_POP_BROAD,2.4"
)
DEMOGRAPHY_DATASET_ID = "DSD_REG_DEMO@DF_DEMO"
DEMOGRAPHY_DATASET_VERSION = "2.0"
DEMOGRAPHY_BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_DEMO@DF_DEMO,2.0"
)
LABOUR_DATASET_ID = "DSD_REG_LAB@DF_RATES"
LABOUR_DATASET_VERSION = "2.4"
GDP_DATASET_ID = "DSD_REG_ECO@DF_GDP"
GDP_DATASET_VERSION = "2.4"
INCOME_DATASET_ID = "DSD_REG_ECO@DF_INC"
INCOME_DATASET_VERSION = "2.4"
LABOUR_BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_LAB@DF_RATES,2.4"
)
GDP_BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_ECO@DF_GDP,2.4"
)
INCOME_BASE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CFE.EDS,DSD_REG_ECO@DF_INC,2.4"
)

DENSITY_DEFAULT_KEY = "A.TL2+TL3......PS_KM2"
POPULATION_DEFAULT_KEY = "A.TL2+TL3...POP._T._T."
DEMOGRAPHY_DEFAULT_KEY = (
    "A.TL2+TL3..."
    "INMIG+OUTMIG+NETMOB+MORT_STANDARD_RATIO"
    "._T._T."
)
LABOUR_DEFAULT_KEY = "A.TL2+TL3...EMP_RATIO+UNE_RATE.Y15T64._T."
GDP_DEFAULT_KEY = "A.TL2+TL3...GDP..Q.USD_PPP_PS"
INCOME_DEFAULT_KEY = "A.TL2+TL3...B6N..Q.USD_PPP_PS"

LABOUR_METRICS = {
    ("EMP_RATIO", "PT_POP_SUB"): {
        "indicator_id": "regional_employment_to_population_ratio",
        "unit": "percent",
    },
    ("UNE_RATE", "PT_LF_SUB"): {
        "indicator_id": "regional_unemployment_rate_oecd",
        "unit": "percent",
    },
}

DEMOGRAPHY_METRICS = {
    ("INMIG", "PT_POP"): {
        "indicator_id": "regional_international_inmigration_share",
        "unit": "percent",
    },
    ("OUTMIG", "PT_POP"): {
        "indicator_id": "regional_international_outmigration_share",
        "unit": "percent",
    },
    ("NETMOB", "PT_POP"): {
        "indicator_id": "regional_net_internal_mobility_share",
        "unit": "percent",
    },
    ("MORT_STANDARD_RATIO", "10P3HB"): {
        "indicator_id": "regional_age_adjusted_mortality_per_1000",
        "unit": "per_1000_people",
    },
}

PARAMS = {
    "dimensionAtObservation": "AllDimensions",
    "format": "csvfilewithlabels",
}


def _first_present(record: dict, candidates: tuple[str, ...]) -> str | None:
    for key in candidates:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _reference_name(record: dict, code: str) -> str:
    candidates = (
        "Reference area",
        "REF_AREA_LABEL",
        "REF_AREA_NAME",
        "Reference Area",
    )
    return _first_present(record, candidates) or code


class OECDRegionalAdapter:
    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout_seconds: float = 120.0,
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

    def fetch_density(
        self,
        *,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = DENSITY_DEFAULT_KEY,
    ) -> str:
        params = {
            **PARAMS,
            "startPeriod": str(start_year),
        }
        if end_year is not None:
            params["endPeriod"] = str(end_year)

        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(
                    f"{DENSITY_BASE_URL}/{key}",
                    params=params,
                )
                response.raise_for_status()

                text = response.text
                if "REF_AREA" not in text or "OBS_VALUE" not in text:
                    raise ValueError("Unexpected OECD regional density CSV schema")

                return text

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

        raise RuntimeError("OECD regional density request failed without an exception")

    def fetch_population(
        self,
        *,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = POPULATION_DEFAULT_KEY,
    ) -> str:
        params = {
            **PARAMS,
            "startPeriod": str(start_year),
        }
        if end_year is not None:
            params["endPeriod"] = str(end_year)

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(
                    f"{POPULATION_BASE_URL}/{key}",
                    params=params,
                )
                response.raise_for_status()
                text = response.text
                if (
                    "REF_AREA" not in text
                    or "OBS_VALUE" not in text
                    or "MEASURE" not in text
                ):
                    raise ValueError(
                        "Unexpected OECD regional population CSV schema"
                    )
                return text
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
        raise RuntimeError(
            "OECD regional population request failed without an exception"
        )

    def fetch_demography(
        self,
        *,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = DEMOGRAPHY_DEFAULT_KEY,
    ) -> str:
        params = {
            **PARAMS,
            "startPeriod": str(start_year),
        }
        if end_year is not None:
            params["endPeriod"] = str(end_year)

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(
                    f"{DEMOGRAPHY_BASE_URL}/{key}",
                    params=params,
                )
                response.raise_for_status()
                text = response.text
                if (
                    "REF_AREA" not in text
                    or "OBS_VALUE" not in text
                    or "MEASURE" not in text
                    or "UNIT_MEASURE" not in text
                ):
                    raise ValueError(
                        "Unexpected OECD regional demography CSV schema"
                    )
                return text
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
        raise RuntimeError(
            "OECD regional demography request failed without an exception"
        )

    def fetch_labour(
        self,
        *,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = LABOUR_DEFAULT_KEY,
    ) -> str:
        params = {
            **PARAMS,
            "startPeriod": str(start_year),
        }
        if end_year is not None:
            params["endPeriod"] = str(end_year)

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(
                    f"{LABOUR_BASE_URL}/{key}",
                    params=params,
                )
                response.raise_for_status()
                text = response.text
                if (
                    "REF_AREA" not in text
                    or "OBS_VALUE" not in text
                    or "MEASURE" not in text
                    or "UNIT_MEASURE" not in text
                ):
                    raise ValueError(
                        "Unexpected OECD regional labour CSV schema"
                    )
                return text
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
        raise RuntimeError(
            "OECD regional labour request failed without an exception"
        )

    def fetch_gdp(
        self,
        *,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = GDP_DEFAULT_KEY,
    ) -> str:
        params = {
            **PARAMS,
            "startPeriod": str(start_year),
        }
        if end_year is not None:
            params["endPeriod"] = str(end_year)

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(
                    f"{GDP_BASE_URL}/{key}",
                    params=params,
                )
                response.raise_for_status()
                text = response.text
                if (
                    "REF_AREA" not in text
                    or "OBS_VALUE" not in text
                    or "MEASURE" not in text
                    or "UNIT_MEASURE" not in text
                ):
                    raise ValueError("Unexpected OECD regional GDP CSV schema")
                return text
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
        raise RuntimeError("OECD regional GDP request failed without an exception")

    def fetch_income(
        self,
        *,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = INCOME_DEFAULT_KEY,
    ) -> str:
        params = {
            **PARAMS,
            "startPeriod": str(start_year),
        }
        if end_year is not None:
            params["endPeriod"] = str(end_year)

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(
                    f"{INCOME_BASE_URL}/{key}",
                    params=params,
                )
                response.raise_for_status()
                text = response.text
                if (
                    "REF_AREA" not in text
                    or "OBS_VALUE" not in text
                    or "MEASURE" not in text
                    or "UNIT_MEASURE" not in text
                ):
                    raise ValueError(
                        "Unexpected OECD regional income CSV schema"
                    )
                return text
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
        raise RuntimeError(
            "OECD regional income request failed without an exception"
        )

    def normalize_density(
        self,
        csv_text: str,
        *,
        allowed_country_iso3: set[str] | None = None,
    ) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        retrieved_at = datetime.now(timezone.utc)
        allowed = (
            {code.upper() for code in allowed_country_iso3}
            if allowed_country_iso3 is not None
            else None
        )
        rows: list[dict] = []

        for record in reader:
            level = str(record.get("TERRITORIAL_LEVEL") or "").upper()
            if level not in {"TL2", "TL3"}:
                continue

            unit = str(record.get("UNIT_MEASURE") or "").upper()
            if unit != "PS_KM2":
                continue

            geo_code = str(record.get("REF_AREA") or "").upper()
            if not geo_code:
                continue

            country_iso3 = str(record.get("COUNTRY") or "").upper() or None
            if allowed is not None and country_iso3 not in allowed:
                continue

            period = str(record.get("TIME_PERIOD") or "")
            raw_value = record.get("OBS_VALUE")
            if not period.isdigit() or raw_value in (None, ""):
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            rows.append(
                {
                    "geo_code": geo_code,
                    "geo_name": _reference_name(record, geo_code),
                    "geo_level": level.lower(),
                    "indicator_id": "regional_population_density",
                    "period": int(period),
                    "value": value,
                    "unit": "people_per_km2",
                    "source_id": SOURCE_ID,
                    "dataset_id": DATASET_ID,
                    "retrieved_at": retrieved_at,
                    "source_updated_at": DATASET_VERSION,
                    "country_iso3": country_iso3,
                    "country_iso2": geo_code[:2] if len(geo_code) >= 2 else None,
                    "geography_system": GEOGRAPHY_SYSTEM,
                    "source_geo_code": geo_code,
                }
            )

        return rows

    def normalize_population(
        self,
        csv_text: str,
        *,
        allowed_country_iso3: set[str] | None = None,
    ) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        retrieved_at = datetime.now(timezone.utc)
        allowed = (
            {code.upper() for code in allowed_country_iso3}
            if allowed_country_iso3 is not None
            else None
        )
        rows: list[dict] = []

        for record in reader:
            level = str(record.get("TERRITORIAL_LEVEL") or "").upper()
            if level not in {"TL2", "TL3"}:
                continue
            if str(record.get("MEASURE") or "").upper() != "POP":
                continue
            if str(record.get("AGE") or "").upper() not in {"_T", "TOTAL"}:
                continue
            if str(record.get("SEX") or "").upper() not in {"_T", "T", "TOTAL"}:
                continue

            geo_code = str(record.get("REF_AREA") or "").upper()
            country_iso3 = str(record.get("COUNTRY") or "").upper() or None
            if not geo_code:
                continue
            if allowed is not None and country_iso3 not in allowed:
                continue

            period = str(record.get("TIME_PERIOD") or "")
            raw_value = record.get("OBS_VALUE")
            if not period.isdigit() or raw_value in (None, ""):
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            rows.append(
                {
                    "geo_code": geo_code,
                    "geo_name": _reference_name(record, geo_code),
                    "geo_level": level.lower(),
                    "indicator_id": "regional_population",
                    "period": int(period),
                    "value": value,
                    "unit": "persons",
                    "source_id": SOURCE_ID,
                    "dataset_id": POPULATION_DATASET_ID,
                    "retrieved_at": retrieved_at,
                    "source_updated_at": DATASET_VERSION,
                    "country_iso3": country_iso3,
                    "country_iso2": geo_code[:2] if len(geo_code) >= 2 else None,
                    "geography_system": GEOGRAPHY_SYSTEM,
                    "source_geo_code": geo_code,
                }
            )

        return rows

    def sync_population(
        self,
        *,
        allowed_country_iso3: set[str] | None = None,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = POPULATION_DEFAULT_KEY,
    ) -> dict:
        csv_text = self.fetch_population(
            start_year=start_year,
            end_year=end_year,
            key=key,
        )
        rows = self.normalize_population(
            csv_text,
            allowed_country_iso3=allowed_country_iso3,
        )
        inserted = upsert_subnational_observations(rows)
        return {
            "source_id": SOURCE_ID,
            "dataset_id": POPULATION_DATASET_ID,
            "dataset_version": DATASET_VERSION,
            "rows": inserted,
            "country_count": len({
                row["country_iso3"]
                for row in rows
                if row.get("country_iso3")
            }),
            "geography_count": len({
                row["geo_code"]
                for row in rows
            }),
            "geo_levels": sorted({
                row["geo_level"]
                for row in rows
            }),
            "period_min": min(
                (row["period"] for row in rows),
                default=None,
            ),
            "period_max": max(
                (row["period"] for row in rows),
                default=None,
            ),
            "complete": bool(rows),
        }

    def normalize_demography(
        self,
        csv_text: str,
        *,
        allowed_country_iso3: set[str] | None = None,
    ) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        retrieved_at = datetime.now(timezone.utc)
        allowed = (
            {code.upper() for code in allowed_country_iso3}
            if allowed_country_iso3 is not None
            else None
        )
        rows: list[dict] = []

        for record in reader:
            level = str(record.get("TERRITORIAL_LEVEL") or "").upper()
            if level not in {"TL2", "TL3"}:
                continue
            if str(record.get("AGE") or "").upper() not in {"_T", "TOTAL"}:
                continue
            if str(record.get("SEX") or "").upper() not in {"_T", "T", "TOTAL"}:
                continue

            measure = str(record.get("MEASURE") or "").upper()
            unit_code = str(record.get("UNIT_MEASURE") or "").upper()
            metric = DEMOGRAPHY_METRICS.get((measure, unit_code))
            if metric is None:
                continue

            geo_code = str(record.get("REF_AREA") or "").upper()
            country_iso3 = str(record.get("COUNTRY") or "").upper() or None
            if not geo_code:
                continue
            if allowed is not None and country_iso3 not in allowed:
                continue

            period = str(record.get("TIME_PERIOD") or "")
            raw_value = record.get("OBS_VALUE")
            if not period.isdigit() or raw_value in (None, "", ".."):
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            rows.append(
                {
                    "geo_code": geo_code,
                    "geo_name": _reference_name(record, geo_code),
                    "geo_level": level.lower(),
                    "indicator_id": metric["indicator_id"],
                    "period": int(period),
                    "value": value,
                    "unit": metric["unit"],
                    "source_id": SOURCE_ID,
                    "dataset_id": DEMOGRAPHY_DATASET_ID,
                    "retrieved_at": retrieved_at,
                    "source_updated_at": DEMOGRAPHY_DATASET_VERSION,
                    "country_iso3": country_iso3,
                    "country_iso2": geo_code[:2] if len(geo_code) >= 2 else None,
                    "geography_system": GEOGRAPHY_SYSTEM,
                    "source_geo_code": geo_code,
                }
            )

        return rows

    def sync_demography(
        self,
        *,
        allowed_country_iso3: set[str] | None = None,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = DEMOGRAPHY_DEFAULT_KEY,
    ) -> dict:
        csv_text = self.fetch_demography(
            start_year=start_year,
            end_year=end_year,
            key=key,
        )
        rows = self.normalize_demography(
            csv_text,
            allowed_country_iso3=allowed_country_iso3,
        )
        inserted = upsert_subnational_observations(rows)
        return {
            "source_id": SOURCE_ID,
            "dataset_id": DEMOGRAPHY_DATASET_ID,
            "dataset_version": DEMOGRAPHY_DATASET_VERSION,
            "rows": inserted,
            "country_count": len({
                row["country_iso3"]
                for row in rows
                if row.get("country_iso3")
            }),
            "geography_count": len({
                row["geo_code"]
                for row in rows
            }),
            "indicator_ids": sorted({
                row["indicator_id"]
                for row in rows
            }),
            "geo_levels": sorted({
                row["geo_level"]
                for row in rows
            }),
            "period_min": min(
                (row["period"] for row in rows),
                default=None,
            ),
            "period_max": max(
                (row["period"] for row in rows),
                default=None,
            ),
            "complete": bool(rows),
        }

    def normalize_labour(
        self,
        csv_text: str,
        *,
        allowed_country_iso3: set[str] | None = None,
    ) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        retrieved_at = datetime.now(timezone.utc)
        allowed = (
            {code.upper() for code in allowed_country_iso3}
            if allowed_country_iso3 is not None
            else None
        )
        rows: list[dict] = []

        for record in reader:
            level = str(record.get("TERRITORIAL_LEVEL") or "").upper()
            if level not in {"TL2", "TL3"}:
                continue
            measure = str(record.get("MEASURE") or "").upper()
            unit_code = str(record.get("UNIT_MEASURE") or "").upper()
            metric = LABOUR_METRICS.get((measure, unit_code))
            if metric is None:
                continue
            if str(record.get("AGE") or "").upper() != "Y15T64":
                continue
            if str(record.get("SEX") or "").upper() not in {"_T", "T", "TOTAL"}:
                continue

            geo_code = str(record.get("REF_AREA") or "").upper()
            country_iso3 = str(record.get("COUNTRY") or "").upper() or None
            if not geo_code:
                continue
            if allowed is not None and country_iso3 not in allowed:
                continue

            period = str(record.get("TIME_PERIOD") or "")
            raw_value = record.get("OBS_VALUE")
            if not period.isdigit() or raw_value in (None, "", ".."):
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            rows.append({
                "geo_code": geo_code,
                "geo_name": _reference_name(record, geo_code),
                "geo_level": level.lower(),
                "indicator_id": metric["indicator_id"],
                "period": int(period),
                "value": value,
                "unit": metric["unit"],
                "source_id": SOURCE_ID,
                "dataset_id": LABOUR_DATASET_ID,
                "retrieved_at": retrieved_at,
                "source_updated_at": LABOUR_DATASET_VERSION,
                "country_iso3": country_iso3,
                "country_iso2": geo_code[:2] if len(geo_code) >= 2 else None,
                "geography_system": GEOGRAPHY_SYSTEM,
                "source_geo_code": geo_code,
            })

        return rows

    def sync_labour(
        self,
        *,
        allowed_country_iso3: set[str] | None = None,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = LABOUR_DEFAULT_KEY,
    ) -> dict:
        csv_text = self.fetch_labour(
            start_year=start_year,
            end_year=end_year,
            key=key,
        )
        rows = self.normalize_labour(
            csv_text,
            allowed_country_iso3=allowed_country_iso3,
        )
        inserted = upsert_subnational_observations(rows)
        return {
            "source_id": SOURCE_ID,
            "dataset_id": LABOUR_DATASET_ID,
            "dataset_version": LABOUR_DATASET_VERSION,
            "rows": inserted,
            "country_count": len({
                row["country_iso3"]
                for row in rows
                if row.get("country_iso3")
            }),
            "geography_count": len({row["geo_code"] for row in rows}),
            "geo_levels": sorted({row["geo_level"] for row in rows}),
            "indicator_ids": sorted({row["indicator_id"] for row in rows}),
            "period_min": min((row["period"] for row in rows), default=None),
            "period_max": max((row["period"] for row in rows), default=None),
            "complete": bool(rows),
        }

    def normalize_gdp(
        self,
        csv_text: str,
        *,
        allowed_country_iso3: set[str] | None = None,
    ) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        retrieved_at = datetime.now(timezone.utc)
        allowed = (
            {code.upper() for code in allowed_country_iso3}
            if allowed_country_iso3 is not None
            else None
        )
        rows: list[dict] = []

        for record in reader:
            level = str(record.get("TERRITORIAL_LEVEL") or "").upper()
            if level not in {"TL2", "TL3"}:
                continue
            if str(record.get("MEASURE") or "").upper() != "GDP":
                continue
            if str(record.get("PRICE_BASE") or "").upper() not in {"Q", "CONSTANT"}:
                continue
            if str(record.get("UNIT_MEASURE") or "").upper() != "USD_PPP_PS":
                continue

            geo_code = str(record.get("REF_AREA") or "").upper()
            country_iso3 = str(record.get("COUNTRY") or "").upper() or None
            if not geo_code:
                continue
            if allowed is not None and country_iso3 not in allowed:
                continue

            period = str(record.get("TIME_PERIOD") or "")
            raw_value = record.get("OBS_VALUE")
            if not period.isdigit() or raw_value in (None, "", ".."):
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            rows.append({
                "geo_code": geo_code,
                "geo_name": _reference_name(record, geo_code),
                "geo_level": level.lower(),
                "indicator_id": "regional_gdp_per_capita_ppp_usd",
                "period": int(period),
                "value": value,
                "unit": "usd_ppp_per_person",
                "source_id": SOURCE_ID,
                "dataset_id": GDP_DATASET_ID,
                "retrieved_at": retrieved_at,
                "source_updated_at": GDP_DATASET_VERSION,
                "country_iso3": country_iso3,
                "country_iso2": geo_code[:2] if len(geo_code) >= 2 else None,
                "geography_system": GEOGRAPHY_SYSTEM,
                "source_geo_code": geo_code,
            })

        return rows

    def sync_gdp(
        self,
        *,
        allowed_country_iso3: set[str] | None = None,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = GDP_DEFAULT_KEY,
    ) -> dict:
        csv_text = self.fetch_gdp(
            start_year=start_year,
            end_year=end_year,
            key=key,
        )
        rows = self.normalize_gdp(
            csv_text,
            allowed_country_iso3=allowed_country_iso3,
        )
        inserted = upsert_subnational_observations(rows)
        return {
            "source_id": SOURCE_ID,
            "dataset_id": GDP_DATASET_ID,
            "dataset_version": GDP_DATASET_VERSION,
            "rows": inserted,
            "country_count": len({
                row["country_iso3"]
                for row in rows
                if row.get("country_iso3")
            }),
            "geography_count": len({row["geo_code"] for row in rows}),
            "geo_levels": sorted({row["geo_level"] for row in rows}),
            "indicator_ids": sorted({row["indicator_id"] for row in rows}),
            "period_min": min((row["period"] for row in rows), default=None),
            "period_max": max((row["period"] for row in rows), default=None),
            "complete": bool(rows),
        }

    def normalize_income(
        self,
        csv_text: str,
        *,
        allowed_country_iso3: set[str] | None = None,
    ) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        retrieved_at = datetime.now(timezone.utc)
        allowed = (
            {code.upper() for code in allowed_country_iso3}
            if allowed_country_iso3 is not None
            else None
        )
        rows: list[dict] = []

        for record in reader:
            level = str(record.get("TERRITORIAL_LEVEL") or "").upper()
            if level not in {"TL2", "TL3"}:
                continue
            if str(record.get("MEASURE") or "").upper() != "B6N":
                continue
            if str(record.get("PRICE_BASE") or "").upper() not in {"Q", "CONSTANT"}:
                continue
            if str(record.get("UNIT_MEASURE") or "").upper() != "USD_PPP_PS":
                continue

            geo_code = str(record.get("REF_AREA") or "").upper()
            country_iso3 = str(record.get("COUNTRY") or "").upper() or None
            if not geo_code:
                continue
            if allowed is not None and country_iso3 not in allowed:
                continue

            period = str(record.get("TIME_PERIOD") or "")
            raw_value = record.get("OBS_VALUE")
            if not period.isdigit() or raw_value in (None, "", ".."):
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            rows.append({
                "geo_code": geo_code,
                "geo_name": _reference_name(record, geo_code),
                "geo_level": level.lower(),
                "indicator_id": "regional_disposable_income_ppp_usd",
                "period": int(period),
                "value": value,
                "unit": "usd_ppp_per_person",
                "source_id": SOURCE_ID,
                "dataset_id": INCOME_DATASET_ID,
                "retrieved_at": retrieved_at,
                "source_updated_at": INCOME_DATASET_VERSION,
                "country_iso3": country_iso3,
                "country_iso2": geo_code[:2] if len(geo_code) >= 2 else None,
                "geography_system": GEOGRAPHY_SYSTEM,
                "source_geo_code": geo_code,
            })

        return rows

    def sync_income(
        self,
        *,
        allowed_country_iso3: set[str] | None = None,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = INCOME_DEFAULT_KEY,
    ) -> dict:
        csv_text = self.fetch_income(
            start_year=start_year,
            end_year=end_year,
            key=key,
        )
        rows = self.normalize_income(
            csv_text,
            allowed_country_iso3=allowed_country_iso3,
        )
        inserted = upsert_subnational_observations(rows)
        return {
            "source_id": SOURCE_ID,
            "dataset_id": INCOME_DATASET_ID,
            "dataset_version": INCOME_DATASET_VERSION,
            "rows": inserted,
            "country_count": len({
                row["country_iso3"]
                for row in rows
                if row.get("country_iso3")
            }),
            "geography_count": len({row["geo_code"] for row in rows}),
            "geo_levels": sorted({row["geo_level"] for row in rows}),
            "indicator_ids": sorted({row["indicator_id"] for row in rows}),
            "period_min": min((row["period"] for row in rows), default=None),
            "period_max": max((row["period"] for row in rows), default=None),
            "complete": bool(rows),
        }

    def sync_density(
        self,
        *,
        allowed_country_iso3: set[str] | None = None,
        start_year: int = 2021,
        end_year: int | None = None,
        key: str = DENSITY_DEFAULT_KEY,
    ) -> dict:
        csv_text = self.fetch_density(
            start_year=start_year,
            end_year=end_year,
            key=key,
        )
        rows = self.normalize_density(
            csv_text,
            allowed_country_iso3=allowed_country_iso3,
        )
        inserted = upsert_subnational_observations(rows)

        countries = sorted({
            row["country_iso3"]
            for row in rows
            if row.get("country_iso3")
        })
        levels = sorted({row["geo_level"] for row in rows})
        geographies = sorted({row["geo_code"] for row in rows})
        periods = sorted({row["period"] for row in rows})

        return {
            "source_id": SOURCE_ID,
            "dataset_id": DATASET_ID,
            "dataset_version": DATASET_VERSION,
            "rows": inserted,
            "country_count": len(countries),
            "countries": countries,
            "geography_count": len(geographies),
            "geo_levels": levels,
            "period_min": min(periods) if periods else None,
            "period_max": max(periods) if periods else None,
            "complete": bool(rows),
        }
