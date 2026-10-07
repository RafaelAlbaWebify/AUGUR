from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.config import settings
from app.db.bootstrap import datastore_status
from app.db.profile import get_profile, save_profile
from app.models.profile import PersonalProfile, PersonalProfileResponse
from app.db.analytics import (
    analytical_evidence_status,
    indicator_source_comparison,
    source_quality_summary,
    official_forecasts,
    country_indicator_series,
    subnational_storage_status,
)
from app.services.country import country_snapshot, list_countries
from app.services.trends import country_trends
from app.services.assessment import country_assessment
from app.services.trajectory import country_future_trajectory
from app.services.scenarios import country_scenarios
from app.services.compare import country_comparison
from app.services.personalized_compare import personalized_normalization
from app.services.profile_readiness import profile_readiness
from app.services.financial_fit import financial_fit
from app.services.legal_fit import legal_fit
from app.services.language_fit import language_fit
from app.services.career_fit import career_fit
from app.esco_store import esco_status
from app.services.ttv import ttv_status
from app.services.ttv_calibration import (
    active_calibration_observation,
    start_calibration_observation,
    complete_calibration_observation,
    cancel_calibration_observation,
    export_development_calibration_package,
    import_development_calibration_package,
)
from app.services.operability import operability_status
from app.services.regional_evidence import regional_evidence, regional_comparison, geographic_level
from app.services.city_evidence import city_evidence

router = APIRouter()


class TTVCalibrationCompleteRequest(BaseModel):
    observed_at: str | None = None


class TTVCalibrationImportRequest(BaseModel):
    exchange_version: str
    schema_version: str | None = None
    scope_id: str | None = None
    privacy: dict | None = None
    case_count: int | None = None
    cases: list[dict]
    notes: list[str] | None = None



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


@router.get("/evidence/status")
def evidence_status_get():
    return {
        **analytical_evidence_status(),
        "esco": esco_status(),
    }


@router.get("/operability")
def operability_get():
    return operability_status()


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


@router.get("/countries/{country_iso3}/overview-series")
def overview_series(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    rows = country_indicator_series(country_iso3, max_points=8)

    grouped: dict[str, dict] = {}
    for row in rows:
        item = grouped.setdefault(
            row["indicator_id"],
            {
                "indicator_id": row["indicator_id"],
                "name": row["name"],
                "dimension": row["dimension"],
                "unit": row["unit"],
                "source_id": row["source_id"],
                "points": [],
            },
        )
        item["points"].append(
            {
                "period": row["period"],
                "value": row["value"],
            }
        )

    return {
        "country_iso3": country_iso3,
        "series": list(grouped.values()),
    }


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




@router.get("/compare/personalized")
def compare_personalized(
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
            detail="At least two countries are required for personalized comparison",
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

    return personalized_normalization(requested)


@router.get("/subnational/status")
def subnational_status_get():
    return {
        **subnational_storage_status(),
        "model_countries": ["ESP", "IRL"],
        "storage": "duckdb",
    }


@router.get("/cities/{city_code}/evidence")
def city_evidence_get(city_code: str):
    city_code = city_code.strip().upper()
    supported_iso2 = {country["iso2"] for country in list_countries()}

    if len(city_code) != 6 or not city_code.endswith("C"):
        raise HTTPException(
            status_code=400,
            detail="City code must be an Urban Audit city code such as ES001C",
        )

    if city_code[:2] not in supported_iso2:
        raise HTTPException(
            status_code=404,
            detail="City is outside AUGUR's registered countries",
        )

    return city_evidence(city_code)


@router.get("/regions/{geo_code}/evidence")
def region_evidence_get(geo_code: str):
    geo_code = geo_code.strip().upper()
    supported_iso2 = {country["iso2"] for country in list_countries()}

    if geographic_level(geo_code) not in {"nuts2", "nuts3"}:
        raise HTTPException(
            status_code=400,
            detail="Regional evidence currently supports NUTS 2 and NUTS 3 codes",
        )

    if geo_code[:2] not in supported_iso2:
        raise HTTPException(
            status_code=404,
            detail="Region is outside AUGUR's registered countries",
        )

    return regional_evidence(geo_code)


@router.get("/regions/compare")
def regions_compare_get(
    regions: str = Query(
        ...,
        description="Comma-separated NUTS 2 or NUTS 3 codes",
    )
):
    requested = [
        value.strip().upper()
        for value in regions.split(",")
        if value.strip()
    ]

    if len(requested) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two regions are required for comparison",
        )

    if len(requested) > 5:
        raise HTTPException(
            status_code=400,
            detail="A maximum of five regions can be compared at once",
        )

    levels = {geographic_level(code) for code in requested}
    if "unknown" in levels:
        raise HTTPException(
            status_code=400,
            detail="Only NUTS 2 and NUTS 3 region codes are supported",
        )

    supported_iso2 = {country["iso2"] for country in list_countries()}
    unsupported = [
        code for code in requested
        if code[:2] not in supported_iso2
    ]
    if unsupported:
        raise HTTPException(
            status_code=404,
            detail=f"Regions are outside AUGUR's registered countries: {', '.join(unsupported)}",
        )

    return regional_comparison(requested)


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



@router.get("/countries/{country_iso3}/ttv")
def ttv_get(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return ttv_status(get_profile(), country_iso3)


@router.get("/countries/{country_iso3}/ttv/calibration/active")
def ttv_calibration_active_get(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return {
        "country_iso3": country_iso3,
        "observation": active_calibration_observation(country_iso3),
    }


@router.post("/countries/{country_iso3}/ttv/calibration/start")
def ttv_calibration_start_post(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    try:
        result = start_calibration_observation(
            country_iso3,
            ttv_status(get_profile(), country_iso3),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "country_iso3": country_iso3,
        "observation": result,
    }


@router.post("/ttv/calibration/{case_id}/complete")
def ttv_calibration_complete_post(
    case_id: str,
    payload: TTVCalibrationCompleteRequest,
):
    try:
        return complete_calibration_observation(
            case_id,
            observed_at=payload.observed_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/ttv/calibration/{case_id}/cancel")
def ttv_calibration_cancel_post(case_id: str):
    try:
        return cancel_calibration_observation(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/ttv/calibration/export")
def ttv_calibration_export_get():
    return export_development_calibration_package()


@router.post("/ttv/calibration/import")
def ttv_calibration_import_post(payload: TTVCalibrationImportRequest):
    try:
        return import_development_calibration_package(
            payload.model_dump()
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc



@router.get("/countries/{country_iso3}/language-fit")
def language_fit_get(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return language_fit(get_profile(), country_iso3)



@router.get("/countries/{country_iso3}/career-fit")
def career_fit_get(country_iso3: str):
    country_iso3 = country_iso3.upper()
    registry = {country["iso3"] for country in list_countries()}

    if country_iso3 not in registry:
        raise HTTPException(status_code=404, detail="Country is not registered")

    return career_fit(get_profile(), country_iso3)



@router.get("/esco/status")
def esco_status_get():
    return esco_status()
