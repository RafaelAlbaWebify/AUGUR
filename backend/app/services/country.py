from app.catalog import COUNTRY_BY_ISO3
from app.db.analytics import (
    country_analysis_coverage,
    country_record,
    latest_observations,
)


def list_countries() -> list[dict]:
    return country_analysis_coverage()


def country_metadata(country_iso3: str) -> dict:
    code = country_iso3.upper()
    stored = country_record(code)
    catalog = COUNTRY_BY_ISO3.get(code)

    if stored is None and catalog is None:
        raise ValueError(f"Country is not registered: {country_iso3}")

    metadata = {
        **(stored or {}),
        **({
            key: value
            for key, value in (catalog or {}).items()
            if value not in (None, [], "")
        }),
    }
    metadata["iso3"] = code
    return metadata


def country_snapshot(country_iso3: str) -> dict:
    observations = latest_observations(country_iso3)

    return {
        "country_iso3": country_iso3.upper(),
        "observation_count": len(observations),
        "indicators": observations,
    }
