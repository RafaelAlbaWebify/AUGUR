from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.db.bootstrap import datastore_status
from app.db.analytics import indicator_source_comparison, source_quality_summary
from app.services.country import country_snapshot, list_countries
from app.services.trends import country_trends
from app.services.assessment import country_assessment

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
