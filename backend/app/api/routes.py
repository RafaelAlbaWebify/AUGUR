import json

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
    environmental_health_burden_status,
    geography_coverage_status,
    geographies_for_country,
    geography_records_by_source_codes,
    geography_geometries_for_country,
    geography_geometry_coverage_status,
)
from app.services.country import (
    country_snapshot,
    list_countries,
    country_coverage_summary,
)
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
    calibration_status,
)
from app.services.operability import operability_status
from app.services.regional_evidence import regional_evidence, regional_comparison, geographic_level
from app.services.city_evidence import city_evidence

router = APIRouter()


class TTVCalibrationCompleteRequest(BaseModel):
    achieved_cefr: str
    evidence_type: str
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


@router.get("/countries/coverage")
def countries_coverage():
    return country_coverage_summary()


@router.get("/geographies/coverage")
def geographies_coverage():
    return geography_coverage_status()


@router.get("/geographies/geometry")
def geographies_geometry(
    country_iso3: str = Query(..., min_length=3, max_length=3),
    geography_system: str | None = Query(default=None),
):
    rows = geography_geometries_for_country(
        country_iso3,
        geography_system=geography_system,
    )
    features = []
    for row in rows:
        geometry = json.loads(row["geometry_geojson"])
        features.append({
            "type": "Feature",
            "id": row["geo_id"],
            "properties": {
                "geo_id": row["geo_id"],
                "country_iso3": row["country_iso3"],
                "geography_system": row["geography_system"],
                "geo_level": row["geo_level"],
                "source_geo_code": row["source_geo_code"],
                "name": row.get("name"),
                "source_id": row["source_id"],
                "dataset_version": row["dataset_version"],
            },
            "geometry": geometry,
        })

    return {
        "type": "FeatureCollection",
        "country_iso3": country_iso3.upper(),
        "geography_system": (
            geography_system.upper()
            if geography_system
            else None
        ),
        "feature_count": len(features),
        "features": features,
    }


@router.get("/geographies/geometry/coverage")
def geographies_geometry_coverage():
    return geography_geometry_coverage_status()


@router.get("/geographies")
def geographies(
    country_iso3: str = Query(..., min_length=3, max_length=3),
    geo_level: str | None = Query(default=None),
):
    return {
        "country_iso3": country_iso3.upper(),
        "geo_level": geo_level.lower() if geo_level else None,
        "geographies": geographies_for_country(
            country_iso3,
            geo_level=geo_level,
        ),
    }


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
        "environmental_health": environmental_health_burden_status(),
        "model_countries": ["ESP", "PRT", "IRL"],
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


@router.get("/geographies/{geo_code}/evidence")
def geography_evidence_get(
    geo_code: str,
    system: str = Query(
        ...,
        description="Registered geography system, e.g. OECD_TL_2024 or OECD_FUA",
    ),
):
    code = geo_code.strip().upper()
    requested_system = system.strip().upper()

    records = [
        record
        for record in geography_records_by_source_codes([code])
        if str(record["geography_system"]).upper() == requested_system
    ]

    if not records:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Geography {code} is not registered in "
                f"{requested_system}"
            ),
        )

    if len(records) > 1:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Geography {code} is ambiguous in "
                f"{requested_system}"
            ),
        )

    return regional_evidence(
        code,
        geography_system=requested_system,
    )


@router.get("/regions/{geo_code}/evidence")
def region_evidence_get(
    geo_code: str,
    system: str | None = Query(
        None,
        description="Optional geography system, e.g. NUTS_2024 or OECD_TL_2024",
    ),
):
    code = geo_code.strip().upper()
    requested_system = system.strip().upper() if system else None

    records = geography_records_by_source_codes([code])
    if requested_system:
        records = [
            record
            for record in records
            if str(record["geography_system"]).upper() == requested_system
        ]

    if not records:
        # Compatibility fallback for pre-registry NUTS installations.
        level = geographic_level(code)
        supported_iso2 = {country["iso2"] for country in list_countries()}
        if (
            requested_system in {None, "NUTS_2024"}
            and level in {"nuts2", "nuts3"}
            and code[:2] in supported_iso2
        ):
            return regional_evidence(
                code,
                geography_system="NUTS_2024",
            )

        raise HTTPException(
            status_code=404,
            detail="Regional geography is not registered with analytical evidence",
        )

    if len(records) > 1 and requested_system is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Regional source code is ambiguous across geography systems; "
                "provide the system query parameter"
            ),
        )

    record = records[0]
    analyzable_countries = {
        country["iso3"]
        for country in list_countries()
    }
    if (
        record.get("country_iso3")
        and record["country_iso3"] not in analyzable_countries
    ):
        raise HTTPException(
            status_code=404,
            detail="Region belongs to a country without analytical coverage",
        )

    return regional_evidence(
        code,
        geography_system=str(record["geography_system"]),
    )


def _compare_registered_geographies(
    requested: list[str],
) -> dict:
    if len(requested) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two geographies are required for comparison",
        )

    if len(requested) > 5:
        raise HTTPException(
            status_code=400,
            detail="A maximum of five geographies can be compared at once",
        )

    records = geography_records_by_source_codes(requested)
    matches_by_code: dict[str, list[dict]] = {
        code: []
        for code in requested
    }
    for record in records:
        code = str(record["source_geo_code"]).upper()
        if code in matches_by_code:
            matches_by_code[code].append(record)

    missing = [
        code
        for code, matches in matches_by_code.items()
        if not matches
    ]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=(
                "Geographies are not registered with analytical metadata: "
                + ", ".join(missing)
            ),
        )

    ambiguous = [
        code
        for code, matches in matches_by_code.items()
        if len(matches) > 1
    ]
    if ambiguous:
        raise HTTPException(
            status_code=409,
            detail=(
                "Source codes are ambiguous across geography systems: "
                + ", ".join(ambiguous)
            ),
        )

    selected = [
        matches_by_code[code][0]
        for code in requested
    ]
    systems = {
        str(record["geography_system"])
        for record in selected
    }
    levels = {
        str(record["geo_level"]).lower()
        for record in selected
    }

    if len(systems) != 1 or len(levels) != 1:
        raise HTTPException(
            status_code=400,
            detail=(
                "Geographic comparison requires the same geography system "
                "and geographic level"
            ),
        )

    system = selected[0]["geography_system"]
    result = regional_comparison(
        requested,
        geography_system=system,
    )
    result["geography_system"] = system
    result["geo_level"] = selected[0]["geo_level"]
    return result


@router.get("/geographies/compare")
def geographies_compare_get(
    geographies: str = Query(
        ...,
        description="Comma-separated source-native geography codes",
    ),
):
    requested = [
        value.strip().upper()
        for value in geographies.split(",")
        if value.strip()
    ]
    return _compare_registered_geographies(requested)


@router.get("/regions/compare")
def regions_compare_get(
    regions: str = Query(
        ...,
        description="Comma-separated regional geography codes",
    )
):
    requested = [
        value.strip().upper()
        for value in regions.split(",")
        if value.strip()
    ]
    return _compare_registered_geographies(requested)


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
            achieved_cefr=payload.achieved_cefr,
            evidence_type=payload.evidence_type,
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


@router.get("/ttv/calibration/status")
def ttv_calibration_status_get():
    return calibration_status()


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
