import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.services.satellite_service import satellite_service
from app.services.susceptibility_service import susceptibility_service
from app.db.database import save_risk_assessment

# Configurable factor weights (normalized dynamically across available factors)
DEFAULT_FACTOR_WEIGHTS: Dict[str, float] = {
    "observed_rainfall": float(os.getenv("WEIGHT_OBSERVED_RAINFALL", "0.30")),
    "forecast_rainfall": float(os.getenv("WEIGHT_FORECAST_RAINFALL", "0.20")),
    "baseline_susceptibility": float(os.getenv("WEIGHT_SUSCEPTIBILITY", "0.25")),
    "terrain": float(os.getenv("WEIGHT_TERRAIN", "0.15")),
    "satellite_detection": float(os.getenv("WEIGHT_SATELLITE_DETECTION", "0.10")),
}

# Configurable provisional category thresholds
THRESHOLD_MODERATE = float(os.getenv("RISK_THRESHOLD_MODERATE", "25.0"))
THRESHOLD_HIGH = float(os.getenv("RISK_THRESHOLD_HIGH", "50.0"))
THRESHOLD_CRITICAL = float(os.getenv("RISK_THRESHOLD_CRITICAL", "75.0"))


def classify_risk_score(score: Optional[float]) -> str:
    if score is None:
        return "INSUFFICIENT_DATA"
    if score >= THRESHOLD_CRITICAL:
        return "CRITICAL"
    if score >= THRESHOLD_HIGH:
        return "HIGH"
    if score >= THRESHOLD_MODERATE:
        return "MODERATE"
    return "LOW"


def _compute_terrain_score(
    elevation_m: Optional[float],
    slope_deg: Optional[float],
) -> Optional[float]:
    """Compute a 0-100 terrain factor ONLY from verified elevation/slope inputs."""
    if slope_deg is None and elevation_m is None:
        return None
    parts: List[float] = []
    if slope_deg is not None:
        # Steep slopes (>35-45 deg) carry elevated instability concern
        parts.append(min(100.0, (max(0.0, slope_deg) / 45.0) * 100.0))
    if elevation_m is not None:
        parts.append(min(100.0, (max(0.0, elevation_m) / 2500.0) * 100.0))
    return round(sum(parts) / len(parts), 2)


def _extract_phase1_evidence(phase1_result_id: Optional[str]) -> Dict[str, Any]:
    """Retrieve verified Phase 1 Prithvi detection evidence without fabricating negatives."""
    if not phase1_result_id:
        return {"available": False, "reason": "No Phase 1 detection ID supplied."}

    meta = satellite_service.get_result_metadata(phase1_result_id)
    if not meta:
        return {"available": False, "reason": f"Phase 1 detection '{phase1_result_id}' not found."}

    det = meta.get("detection", {})
    pct = det.get("landslide_pixel_percentage", 0.0)
    detected = bool(det.get("landslide_detected", False))
    ts_str = meta.get("timestamp")

    # Check freshness of satellite detection
    freshness_note = "Unknown acquisition/processing date"
    age_days: Optional[float] = None
    if ts_str:
        try:
            dt = datetime.fromisoformat(ts_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_days = round((datetime.now(timezone.utc) - dt).total_seconds() / 86400.0, 2)
            freshness_note = f"Processed {age_days} days ago (visible scars, not proof of active movement)"
        except Exception:
            pass

    # Map detected pixel percentage (0-20%+) to a 0-100 evidence score
    score = min(100.0, (pct / 15.0) * 100.0) if detected else 10.0

    return {
        "available": True,
        "result_id": phase1_result_id,
        "model": meta.get("model"),
        "landslide_detected": detected,
        "landslide_pixel_percentage": pct,
        "timestamp": ts_str,
        "age_days": age_days,
        "freshness_note": freshness_note,
        "evidence_score": round(score, 2),
    }


def _extract_phase2_susceptibility(phase2_analysis_id: Optional[str]) -> Dict[str, Any]:
    """Retrieve verified Phase 2 multimodal susceptibility output."""
    if not phase2_analysis_id:
        return {"available": False, "reason": "No Phase 2 susceptibility analysis ID supplied."}

    record = susceptibility_service.get_analysis(phase2_analysis_id)
    if not record:
        return {"available": False, "reason": f"Phase 2 analysis '{phase2_analysis_id}' not found."}

    pred = record.get("prediction", record.get("prediction_output", {}))
    score_01 = pred.get("susceptibility_score")
    if score_01 is None:
        return {"available": False, "reason": "Phase 2 record lacked susceptibility_score."}

    return {
        "available": True,
        "analysis_id": phase2_analysis_id,
        "model_repository": record.get("model_repository"),
        "model_revision": record.get("model_revision"),
        "susceptibility_score_01": float(score_01),
        "susceptibility_class": pred.get("susceptibility_class"),
        "coverage_status": record.get("geographic", {}).get("coverage_status", "uncalibrated_prototype"),
        "created_at": record.get("created_at"),
        "factor_score_100": round(float(score_01) * 100.0, 2),
    }


def _build_explanation(
    risk_category: str,
    risk_score: Optional[float],
    location_label: str,
    rainfall_analysis: Optional[Dict[str, Any]],
    susceptibility_info: Dict[str, Any],
    terrain_info: Dict[str, Any],
    satellite_info: Dict[str, Any],
    missing_factors: List[str],
    completeness_score: float,
) -> str:
    if risk_category == "INSUFFICIENT_DATA":
        return (
            f"Landslide risk for {location_label} cannot be assessed (INSUFFICIENT_DATA) because "
            f"required weather and dynamic trigger inputs are unavailable ({', '.join(missing_factors)}). "
            "No fallback score was fabricated."
        )

    reasons: List[str] = []
    if rainfall_analysis:
        r24 = rainfall_analysis["observed_windows"]["24h"]["rainfall_mm"]
        r72 = rainfall_analysis["observed_windows"]["72h"]["rainfall_mm"]
        f24 = rainfall_analysis["forecast_windows"]["next_24h"]["rainfall_mm"]
        awi = rainfall_analysis["awi_proxy"]["awi_value"]
        if r24 is not None:
            reasons.append(f"24h observed rainfall is {r24} mm (72h: {r72 if r72 is not None else 'N/A'} mm, AWI proxy: {awi if awi is not None else 'N/A'})")
        if f24 is not None:
            reasons.append(f"upcoming 24h forecast rainfall is {f24} mm")

    if susceptibility_info.get("available"):
        reasons.append(
            f"Phase 2 baseline susceptibility is {susceptibility_info['susceptibility_class']} "
            f"(score {susceptibility_info['susceptibility_score_01']:.3f}, uncalibrated prototype)"
        )

    if terrain_info.get("available"):
        reasons.append(
            f"terrain slope is {terrain_info.get('slope_deg', 'N/A')} deg / elevation {terrain_info.get('elevation_m', 'N/A')} m"
        )

    if satellite_info.get("available"):
        reasons.append(
            f"Phase 1 Prithvi imagery shows {'detected landslide features' if satellite_info['landslide_detected'] else 'no detected landslide scars'} "
            f"({satellite_info['landslide_pixel_percentage']}%)"
        )

    reason_text = "; ".join(reasons) if reasons else "limited available factors"
    missing_text = (
        f" Unavailable factors excluded from weighting: {', '.join(missing_factors)}."
        if missing_factors else ""
    )

    return (
        f"Dynamic heuristic risk is currently {risk_category} (index {risk_score:.1f}/100, "
        f"completeness {completeness_score*100:.0f}%) for {location_label} based on: {reason_text}.{missing_text} "
        "This is a provisional heuristic index requiring regional calibration for North Eastern India "
        "and is not a calibrated probability or guarantee of a landslide event."
    )


def compute_dynamic_risk(
    latitude: float,
    longitude: float,
    location_id: str,
    location_name: Optional[str],
    weather_bundle: Dict[str, Any],
    rainfall_analysis: Dict[str, Any],
    phase1_result_id: Optional[str] = None,
    phase2_analysis_id: Optional[str] = None,
    elevation_m: Optional[float] = None,
    slope_deg: Optional[float] = None,
    soil_moisture_m3_m3: Optional[float] = None,
    custom_weights: Optional[Dict[str, float]] = None,
    persist: bool = True,
) -> Dict[str, Any]:
    """
    Fuse available weather, rainfall, terrain, Phase 1 detection, and Phase 2 susceptibility
    using dynamic weight normalization across ONLY available factors.
    """
    weights_cfg = dict(custom_weights or DEFAULT_FACTOR_WEIGHTS)
    warnings: List[str] = list(rainfall_analysis.get("warnings", []))

    obs_rain_score = rainfall_analysis.get("observed_rainfall_score")
    fc_rain_score = rainfall_analysis.get("forecast_rainfall_score")

    phase1_info = _extract_phase1_evidence(phase1_result_id)
    phase2_info = _extract_phase2_susceptibility(phase2_analysis_id)
    terrain_score = _compute_terrain_score(elevation_m, slope_deg)

    terrain_info = {
        "available": terrain_score is not None,
        "elevation_m": elevation_m,
        "slope_deg": slope_deg,
        "terrain_score": terrain_score,
        "soil_moisture_m3_m3": soil_moisture_m3_m3,
    }

    raw_scores: Dict[str, Optional[float]] = {
        "observed_rainfall": obs_rain_score,
        "forecast_rainfall": fc_rain_score,
        "baseline_susceptibility": phase2_info.get("factor_score_100") if phase2_info.get("available") else None,
        "terrain": terrain_score,
        "satellite_detection": phase1_info.get("evidence_score") if phase1_info.get("available") else None,
    }

    missing_factors = [k for k, v in raw_scores.items() if v is None]
    available_factors = {k: v for k, v in raw_scores.items() if v is not None}

    total_cfg_weight = sum(weights_cfg.values())
    avail_cfg_weight = sum(weights_cfg[k] for k in available_factors if k in weights_cfg)
    completeness_score = round(avail_cfg_weight / total_cfg_weight, 3) if total_cfg_weight > 0 else 0.0

    # Insufficient data guard: require at least one dynamic weather signal or sufficient factor coverage
    has_weather = (obs_rain_score is not None) or (fc_rain_score is not None)
    if not has_weather and avail_cfg_weight < 0.25:
        effective_weights: Dict[str, float] = {}
        risk_score: Optional[float] = None
        risk_category = "INSUFFICIENT_DATA"
        warnings.append("Insufficient data: both observed and forecast weather streams failed.")
    else:
        effective_weights = {
            k: round(weights_cfg[k] / avail_cfg_weight, 4)
            for k in available_factors
            if avail_cfg_weight > 0
        }
        risk_score = round(
            sum(available_factors[k] * effective_weights[k] for k in available_factors),
            2,
        )
        risk_category = classify_risk_score(risk_score)

    loc_label = location_name or f"({latitude:.4f}, {longitude:.4f})"
    explanation = _build_explanation(
        risk_category=risk_category,
        risk_score=risk_score,
        location_label=loc_label,
        rainfall_analysis=rainfall_analysis,
        susceptibility_info=phase2_info,
        terrain_info=terrain_info,
        satellite_info=phase1_info,
        missing_factors=missing_factors,
        completeness_score=completeness_score,
    )

    assessment_id = f"risk_{uuid.uuid4().hex[:12]}"
    assessment_time = datetime.now(timezone.utc).isoformat()

    data_sources = list(weather_bundle.get("sources", []))
    if phase2_info.get("available"):
        data_sources.append(f"Phase 2 HF Model ({phase2_info['model_repository']})")
    if phase1_info.get("available"):
        data_sources.append(f"Phase 1 Prithvi ({phase1_info['model']})")
    if terrain_info["available"]:
        data_sources.append("User/GIS Terrain Elevation & Slope")

    data_freshness = {
        "weather_observation_time": weather_bundle.get("current", {}).get("observation_time"),
        "weather_is_stale": weather_bundle.get("current", {}).get("is_stale", True),
        "weather_cached": weather_bundle.get("cached", False),
        "rainfall_completeness": rainfall_analysis.get("data_completeness"),
        "phase1_age_days": phase1_info.get("age_days") if phase1_info.get("available") else None,
        "phase2_created_at": phase2_info.get("created_at") if phase2_info.get("available") else None,
    }

    payload = {
        "success": True,
        "assessment_id": assessment_id,
        "location_id": location_id,
        "location_name": location_name,
        "latitude": latitude,
        "longitude": longitude,
        "risk_score": risk_score,
        "risk_category": risk_category,
        "is_calibrated_probability": False,
        "factor_scores": raw_scores,
        "factor_weights_configured": weights_cfg,
        "factor_weights_effective": effective_weights,
        "missing_factors": missing_factors,
        "completeness_score": completeness_score,
        "rainfall_indicators": rainfall_analysis,
        "susceptibility_info": phase2_info,
        "terrain_info": terrain_info,
        "satellite_detection_evidence": phase1_info,
        "explanation": explanation,
        "data_freshness": data_freshness,
        "data_sources": data_sources,
        "warnings": warnings,
        "assessment_time": assessment_time,
    }

    if persist:
        save_risk_assessment(
            {
                "id": assessment_id,
                "location_id": location_id,
                "latitude": latitude,
                "longitude": longitude,
                "risk_score": risk_score,
                "risk_category": risk_category,
                "factor_scores": raw_scores,
                "factor_weights": effective_weights,
                "missing_factors": missing_factors,
                "explanation": explanation,
                "assessment_time": assessment_time,
                "data_sources": data_sources,
                "completeness_score": completeness_score,
                "raw_payload": payload,
            }
        )

    return payload
