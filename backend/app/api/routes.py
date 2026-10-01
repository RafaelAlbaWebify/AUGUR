from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.db.bootstrap import datastore_status
from app.db.profile import get_profile, save_profile
from app.models.profile import PersonalProfile, PersonalProfileResponse
from app.db.analytics import (
    indicator_source_comparison,
    source_quality_summary,
    official_forecasts,
)
from app.services.country import country_snapshot, list_countries
from app.services.trends import country_trends
from app.services.assessment import country_assessment
from app.services.trajectory import country_future_trajectory
from app.services.scenarios import country_scenarios
from app.services.compare import country_comparison
from app.services.profile_readiness import profile_readiness
from app.services.financial_fit import financial_fit
from app.services.legal_fit import legal_fit

router = APIRouter()


@router.get("/health")
def health():
    stores = datastore_status()
    ok = all(stores.values())
    return {
        "status": "ok" if ok else "degraded",
        "phase": 1,
        "version": "0.1.0-phase1",
        "datastores": stores,
        "paths": {
            "sqlite": str(settings.sqlite_path),
            "duckdb": str(settings.duckdb_path),
        },
    }


@router.get("/countries")
def countries():
    return {"countries": list_countries()}


@router.get("/countries/{country_iso3}/snapshot")
def snapshot(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return country_snapshot(country_iso3)


@router.get("/countries/{country_iso3}/trends")
def trends(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return country_trends(country_iso3)


@router.get("/countries/{country_iso3}/assessment")
def assessment(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return country_assessment(country_iso3)


@router.get("/countries/{country_iso3}/sources")
def source_comparison(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return {
        "country_iso3": country_iso3,
        "observations": indicator_source_comparison(country_iso3),
    }


@router.get("/countries/{country_iso3}/source-quality")
def source_quality(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return {
        "country_iso3": country_iso3,
        "indicators": source_quality_summary(country_iso3),
    }


@router.get("/countries/{country_iso3}/forecasts")
def forecasts(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    rows = official_forecasts(country_iso3)

    return {
        "country_iso3": country_iso3,
        "observation_type": "official_forecast",
        "forecast_count": len(rows),
        "forecasts": rows,
    }


@router.get("/countries/{country_iso3}/trajectory")
def trajectory(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return country_future_trajectory(country_iso3)


@router.get("/countries/{country_iso3}/scenarios")
def scenarios(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return country_scenarios(country_iso3)


@router.get("/compare")
def compare(
    countries: str = Query(
        "ESP,PRT,IRL",
        description="Comma-separated ISO3 country codes",
    )
):
    requested = [
        value.strip().upper()
        for value in countries.split(",")
        if value.strip()
    ]

    if len(requested) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two countries are required for comparison",
        )

    if len(requested) > 5:
        raise HTTPException(
            status_code=400,
            detail="A maximum of five countries can be compared at once",
        )

    registry = {country["iso3"] for country in list_countries()}
    unknown = [code for code in requested if code not in registry]

    if unknown:
        raise HTTPException(
            status_code=404,
            detail=f"Countries are not registered: {', '.join(unknown)}",
        )

    return country_comparison(requested)



@router.get("/profile", response_model=PersonalProfileResponse)
def profile_get():
    return get_profile()


@router.put("/profile", response_model=PersonalProfileResponse)
def profile_put(profile: PersonalProfile):
    return save_profile(profile)



@router.get("/profile/readiness")
def profile_readiness_get():
    return profile_readiness(get_profile())



@router.get("/countries/{country_iso3}/financial-fit")
def financial_fit_get(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return financial_fit(get_profile(), country_iso3)



@router.get("/countries/{country_iso3}/legal-fit")
def legal_fit_get(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return legal_fit(get_profile(), country_iso3)
