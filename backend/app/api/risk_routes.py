from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status

from app.schemas.risk_schema import (
    WeatherCurrentResponse,
    RainfallIndicatorsResponse,
    RiskAnalyzeRequest,
    RiskAssessmentResponse,
    RiskExplanationResponse,
    RiskHistoryResponse,
    RiskHotspotsResponse,
)
from app.services.weather_service import weather_service, make_location_id
from app.ml.landslide_weather_analyzer import analyze_rainfall
from app.ml.landslide_risk_engine import compute_dynamic_risk
from app.db.database import (
    get_latest_risk_by_location,
    get_risk_by_assessment_id,
    get_risk_history_by_id_or_location,
    get_risk_hotspots,
)

router = APIRouter(tags=["Phase 3 — Weather & Dynamic Risk"])


@router.get(
    "/weather/current",
    response_model=WeatherCurrentResponse,
    summary="Retrieve Current Weather (Open-Meteo)",
)
async def get_current_weather(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    location_id: Optional[str] = Query(None),
):
    bundle = await weather_service.fetch_weather_bundle(
        latitude=latitude, longitude=longitude, location_id=location_id
    )
    cur = bundle["current"]
    return WeatherCurrentResponse(
        location_id=bundle["location_id"],
        latitude=latitude,
        longitude=longitude,
        precipitation_mm=cur["precipitation_mm"],
        temperature_c=cur["temperature_c"],
        relative_humidity_pct=cur["relative_humidity_pct"],
        wind_speed_kmh=cur["wind_speed_kmh"],
        weather_code=cur["weather_code"],
        weather_condition=cur["weather_condition"],
        observation_time=cur["observation_time"],
        retrieved_at=bundle["retrieved_at"],
        is_stale=cur["is_stale"],
        cached=bundle["cached"],
        source=", ".join(bundle["sources"]) if bundle["sources"] else "Unavailable",
        warnings=bundle["warnings"],
    )


@router.get(
    "/weather/rainfall",
    response_model=RainfallIndicatorsResponse,
    summary="Retrieve Historical & Forecast Rainfall Indicators",
)
async def get_rainfall_indicators(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    location_id: Optional[str] = Query(None),
):
    bundle = await weather_service.fetch_weather_bundle(
        latitude=latitude, longitude=longitude, location_id=location_id
    )
    analysis = analyze_rainfall(bundle, persist=True)
    return RainfallIndicatorsResponse(**analysis)


@router.post(
    "/risk/analyze",
    response_model=RiskAssessmentResponse,
    summary="Perform Weather-Integrated Dynamic Landslide Risk Assessment",
)
async def analyze_dynamic_risk(req: RiskAnalyzeRequest):
    loc_id = req.location_id or make_location_id(req.latitude, req.longitude)
    bundle = await weather_service.fetch_weather_bundle(
        latitude=req.latitude, longitude=req.longitude, location_id=loc_id
    )
    rainfall_analysis = analyze_rainfall(bundle, persist=True)
    result = compute_dynamic_risk(
        latitude=req.latitude,
        longitude=req.longitude,
        location_id=loc_id,
        location_name=req.location_name,
        weather_bundle=bundle,
        rainfall_analysis=rainfall_analysis,
        phase1_result_id=req.phase1_result_id,
        phase2_analysis_id=req.phase2_analysis_id,
        elevation_m=req.elevation_m,
        slope_deg=req.slope_deg,
        soil_moisture_m3_m3=req.soil_moisture_m3_m3,
        persist=True,
    )
    return RiskAssessmentResponse(**result)


@router.get(
    "/risk/hotspots",
    response_model=RiskHotspotsResponse,
    summary="Retrieve HIGH or CRITICAL Risk Hotspots",
)
async def list_risk_hotspots(limit: int = Query(50, ge=1, le=200)):
    hotspots = get_risk_hotspots(limit=limit)
    return RiskHotspotsResponse(
        count=len(hotspots),
        categories_included=["HIGH", "CRITICAL"],
        hotspots=hotspots,
    )


@router.get(
    "/risk/{location_id}",
    response_model=RiskAssessmentResponse,
    summary="Retrieve Latest Risk Assessment for a Location",
)
async def get_latest_location_risk(location_id: str):
    record = get_latest_risk_by_location(location_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk assessment found for location '{location_id}'.",
        )
    return RiskAssessmentResponse(**record)


@router.get(
    "/risk/{assessment_id}/explain",
    response_model=RiskExplanationResponse,
    summary="Retrieve Explanation for a Risk Assessment",
)
async def explain_risk_assessment(assessment_id: str):
    record = get_risk_by_assessment_id(assessment_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment '{assessment_id}' not found.",
        )
    return RiskExplanationResponse(
        assessment_id=record["assessment_id"],
        location_id=record["location_id"],
        risk_score=record["risk_score"],
        risk_category=record["risk_category"],
        explanation=record["explanation"],
        factor_scores=record["factor_scores"],
        factor_weights_effective=record["factor_weights_effective"],
        missing_factors=record["missing_factors"],
        data_freshness=record["data_freshness"],
        assessment_time=record["assessment_time"],
    )


@router.get(
    "/risk/{assessment_id}/history",
    response_model=RiskHistoryResponse,
    summary="Retrieve Historical Risk Assessments for Location",
)
async def get_assessment_history(assessment_id: str, limit: int = Query(50, ge=1, le=200)):
    history = get_risk_history_by_id_or_location(assessment_id, limit=limit)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No assessment history found for '{assessment_id}'.",
        )
    return RiskHistoryResponse(
        location_id=history[0]["location_id"],
        count=len(history),
        assessments=history,
    )
