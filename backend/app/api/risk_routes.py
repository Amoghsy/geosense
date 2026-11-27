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
    DetailedRiskExplanationResponse,
    ContributingFactorsResponse,
    RiskTrendsResponse,
    RiskComparisonResponse,
)
from app.services.weather_service import weather_service, make_location_id
from app.services.risk_explanation_service import risk_explanation_service
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


# ==========================================
# Phase 5: XAI & Risk Trend Endpoints
# ==========================================

@router.get(
    "/risk/{assessment_id}/explanation",
    response_model=DetailedRiskExplanationResponse,
    tags=["Phase 5 — XAI & Risk Trends"],
    summary="Detailed Explainable AI (XAI) Breakdown for an Assessment",
)
async def get_detailed_explanation(assessment_id: str):
    res = risk_explanation_service.explain_assessment(assessment_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment '{assessment_id}' not found.",
        )
    return DetailedRiskExplanationResponse(**res)


@router.get(
    "/risk/{assessment_id}/contributing-factors",
    response_model=ContributingFactorsResponse,
    tags=["Phase 5 — XAI & Risk Trends"],
    summary="Structured Factor Contributions for an Assessment",
)
async def get_contributing_factors(assessment_id: str):
    res = risk_explanation_service.explain_assessment(assessment_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment '{assessment_id}' not found.",
        )
    return ContributingFactorsResponse(
        assessment_id=res["assessment_id"],
        location_id=res["location_id"],
        risk_score=res["risk_score"],
        risk_category=res["risk_category"],
        factors=res["factor_contributions"],
    )


@router.get(
    "/risk/{location_id}/trends",
    response_model=RiskTrendsResponse,
    tags=["Phase 5 — XAI & Risk Trends"],
    summary="Historical Risk & Rainfall Trends for a Location",
)
async def get_location_risk_trends(
    location_id: str,
    start_date: Optional[str] = Query(None, description="ISO start timestamp"),
    end_date: Optional[str] = Query(None, description="ISO end timestamp"),
):
    res = risk_explanation_service.analyze_trends(
        location_id=location_id, start_date=start_date, end_date=end_date
    )
    return RiskTrendsResponse(**res)


@router.get(
    "/risk/{location_id}/comparison",
    response_model=RiskComparisonResponse,
    tags=["Phase 5 — XAI & Risk Trends"],
    summary="Compare Two Stored Risk Assessments",
)
async def compare_location_assessments(
    location_id: str,
    assessment_id_1: str = Query(..., description="Earlier assessment ID"),
    assessment_id_2: str = Query(..., description="Later assessment ID"),
):
    res = risk_explanation_service.compare_assessments(
        location_id=location_id,
        assessment_id_1=assessment_id_1,
        assessment_id_2=assessment_id_2,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both assessment IDs were not found.",
        )
    return RiskComparisonResponse(**res)
