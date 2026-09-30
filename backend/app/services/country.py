from app.db.analytics import country_registry, latest_observations


def list_countries() -> list[dict]:
    return country_registry()


def country_snapshot(country_iso3: str) -> dict:
    observations = latest_observations(country_iso3)

    return {
        "country_iso3": country_iso3.upper(),
        "observation_count": len(observations),
        "indicators": observations,
    }
