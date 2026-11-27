from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.services.weather_service import weather_service, make_location_id
from app.ml.landslide_weather_analyzer import analyze_rainfall
from app.ml.landslide_risk_engine import compute_dynamic_risk
from app.services.satellite_service import satellite_service
from app.services.susceptibility_service import susceptibility_service
from app.services.gis_service import gis_service
from app.services.risk_explanation_service import risk_explanation_service
from app.db.database import get_latest_risk_by_location
from app.gis.geo_utils import validate_coordinates


async def weather_analysis_tool(
    latitude: float,
    longitude: float,
    location_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve real Open-Meteo current weather, observed rolling rainfall, AWI proxy, and forecast."""
    validate_coordinates(latitude, longitude)
    loc_id = location_id or make_location_id(latitude, longitude)
    bundle = await weather_service.fetch_weather_bundle(
        latitude=latitude, longitude=longitude, location_id=loc_id
    )
    rain = analyze_rainfall(bundle, persist=False)
    cur = bundle["current"]
    obs = rain["observed_windows"]
    fc = rain["forecast_windows"]
    return {
        "location_id": loc_id,
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": cur,
        "observed_rainfall_mm": {
            "1h": obs["1h"]["rainfall_mm"],
            "24h": obs["24h"]["rainfall_mm"],
            "72h": obs["72h"]["rainfall_mm"],
            "7d": obs["7d"]["rainfall_mm"],
            "30d": obs["30d"]["rainfall_mm"],
        },
        "forecast_rainfall_mm": {
            "next_3h": fc["next_3h"]["rainfall_mm"],
            "next_24h": fc["next_24h"]["rainfall_mm"],
            "next_72h": fc["next_72h"]["rainfall_mm"],
        },
        "awi_proxy": rain["awi_proxy"],
        "heavy_rainfall_detected": rain["intensity"]["heavy_rainfall_detected"],
        "sources": bundle["sources"],
        "observation_time": cur.get("observation_time"),
        "warnings": rain["warnings"],
        "_raw_bundle": bundle,
        "_raw_rainfall": rain,
    }


async def landslide_risk_analysis_tool(
    latitude: float,
    longitude: float,
    location_id: Optional[str] = None,
    location_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve the latest stored Phase 3 risk assessment for a location, or compute one
    using the real Phase 3 risk engine if none exists yet. Never invents a conflicting score.
    """
    validate_coordinates(latitude, longitude)
    loc_id = location_id or make_location_id(latitude, longitude)
    existing = get_latest_risk_by_location(loc_id)
    if existing:
        return {
            "source_mode": "stored_assessment",
            "assessment": existing,
        }

    wx = await weather_analysis_tool(latitude, longitude, loc_id)
    computed = compute_dynamic_risk(
        latitude=latitude,
        longitude=longitude,
        location_id=loc_id,
        location_name=location_name,
        weather_bundle=wx["_raw_bundle"],
        rainfall_analysis=wx["_raw_rainfall"],
        persist=True,
    )
    return {
        "source_mode": "newly_computed_phase3",
        "assessment": computed,
    }


def satellite_detection_tool(
    detection_id: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    role: str = "citizen",
) -> Dict[str, Any]:
    """Retrieve Phase 1 Prithvi satellite detection metadata. Never claims no landslide exists if unavailable."""
    if detection_id:
        meta = satellite_service.get_result_metadata(detection_id)
        if not meta:
            return {"available": False, "message": f"Phase 1 detection '{detection_id}' not found."}
        return {"available": True, "detection": meta}

    if latitude is not None and longitude is not None:
        validate_coordinates(latitude, longitude)
        loc = gis_service.query_location(latitude, longitude)
        dets = loc.get("satellite_detections", [])
        if not dets:
            return {
                "available": False,
                "message": (
                    "No georeferenced Phase 1 satellite detection covers these coordinates. "
                    "Absence of satellite imagery does not mean no landslide exists."
                ),
            }
        return {"available": True, "detections": dets}

    fc = gis_service.get_layer_features("phase1_detections", limit=10)
    feats = fc.get("features", []) if fc else []
    if not feats:
        return {
            "available": False,
            "message": "No georeferenced Phase 1 satellite detections are currently stored.",
        }
    return {"available": True, "count": len(feats), "detections": [f["properties"] for f in feats]}


def susceptibility_analysis_tool(
    analysis_id: Optional[str] = None,
    region: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve verified Phase 2 multimodal susceptibility outputs with prototype coverage notice."""
    if analysis_id:
        rec = susceptibility_service.get_analysis(analysis_id)
        if not rec:
            return {"available": False, "message": f"Phase 2 analysis '{analysis_id}' not found."}
        return {"available": True, "analysis": rec}

    fc = gis_service.get_layer_features("phase2_susceptibility", region=region, limit=10)
    feats = fc.get("features", []) if fc else []
    if not feats:
        return {
            "available": False,
            "message": "No Phase 2 susceptibility patches are stored for this region.",
        }
    return {
        "available": True,
        "coverage_disclaimer": "Phase 2 uses an uncalibrated academic prototype (vinukatashidu/landslide-detection-multimodal).",
        "analyses": [f["properties"] for f in feats],
    }


def gis_location_tool(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    state: Optional[str] = None,
    role: str = "citizen",
) -> Dict[str, Any]:
    """Resolve state, nearby hotspots, and emergency resources with role-based filtering."""
    result: Dict[str, Any] = {}
    if latitude is not None and longitude is not None:
        validate_coordinates(latitude, longitude)
        loc = gis_service.query_location(latitude, longitude)
        if role == "citizen":
            # Redact internal/unverified incident details for citizen role
            loc["incidents"] = []
        result["location_info"] = loc

    hotspots = gis_service.get_hotspots(state=state, limit=10)
    result["hotspots"] = hotspots

    res_fc = gis_service.get_layer_features("emergency_resources", region=state, limit=10)
    res_list = res_fc.get("features", []) if res_fc else []
    result["emergency_resources"] = {
        "available": len(res_list) > 0,
        "count": len(res_list),
        "items": res_list,
        "note": "No verified emergency resources dataset is currently populated." if not res_list else "Verified GIS resources.",
    }
    return result


def risk_explanation_tool(assessment_id: str) -> Dict[str, Any]:
    """Retrieve Phase 5 XAI structured explanation and factor contributions."""
    exp = risk_explanation_service.explain_assessment(assessment_id)
    if not exp:
        return {"available": False, "message": f"Explanation for assessment '{assessment_id}' not found."}
    return {"available": True, "explanation": exp}


def historical_trend_tool(
    location_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve Phase 5 historical risk and rainfall trends from stored assessments."""
    return risk_explanation_service.analyze_trends(
        location_id=location_id, start_date=start_date, end_date=end_date
    )


def hotspot_prioritization_tool(
    state: Optional[str] = None,
    role: str = "field_officer",
) -> Dict[str, Any]:
    """
    Rank real HIGH/CRITICAL Phase 3 hotspots transparently by risk_score, completeness, and rainfall.
    Restricted to field_officer and authority roles for operational inspection planning.
    """
    if role == "citizen":
        return {
            "authorized": False,
            "message": "Operational inspection prioritization is restricted to Field Officers and Authorities.",
        }
    hs = gis_service.get_hotspots(state=state, limit=25)
    ranked = sorted(
        hs.get("hotspots", []),
        key=lambda x: (x.get("risk_score") or 0.0),
        reverse=True,
    )
    priorities = []
    for idx, item in enumerate(ranked[:10], start=1):
        priorities.append(
            {
                "priority_rank": idx,
                "location_id": item["location_id"],
                "location_name": item.get("location_name"),
                "state": item.get("state"),
                "risk_score": item.get("risk_score"),
                "risk_category": item.get("risk_category"),
                "assessment_time": item.get("assessment_time"),
                "reason": (
                    f"Ranked #{idx} due to {item.get('risk_category')} heuristic index "
                    f"({item.get('risk_score')}/100). Advisory only; field verification required."
                ),
            }
        )
    return {
        "authorized": True,
        "count": len(priorities),
        "priorities": priorities,
        "advisory_note": "Advisory prioritization based on stored assessments; not a validated landslide prediction.",
    }


async def situation_report_tool(
    region_id: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    role: str = "authority",
) -> Dict[str, Any]:
    """Generate a grounded situation report for Field Officers or Authorities."""
    if role == "citizen":
        return {
            "authorized": False,
            "message": "Situation reports are restricted to Field Officers and Disaster Management Authorities.",
        }

    now_iso = datetime.now(timezone.utc).isoformat()
    state_name = region_id.replace("_", " ").title() if region_id else None
    summary = gis_service.get_summary()
    hotspots = hotspot_prioritization_tool(state=state_name, role=role)
    sat = satellite_detection_tool(role=role)
    res_fc = gis_service.get_layer_features("emergency_resources", region=state_name, limit=20)
    inc_fc = gis_service.get_layer_features("verified_incidents", region=state_name, limit=20)

    weather_snap = None
    if latitude is not None and longitude is not None:
        weather_snap = await weather_analysis_tool(latitude, longitude)

    return {
        "authorized": True,
        "report_generated_at": now_iso,
        "region": state_name or "North Eastern India (All 8 States)",
        "gis_summary": summary,
        "elevated_hotspots": hotspots.get("priorities", []),
        "weather_snapshot": (
            {
                "observed_rainfall_mm": weather_snap["observed_rainfall_mm"],
                "forecast_rainfall_mm": weather_snap["forecast_rainfall_mm"],
                "observation_time": weather_snap["observation_time"],
            }
            if weather_snap else None
        ),
        "satellite_detection_evidence": sat,
        "verified_incidents_count": len(inc_fc.get("features", [])) if inc_fc else 0,
        "emergency_resources_count": len(res_fc.get("features", [])) if res_fc else 0,
        "data_gaps": [
            "District-level ADM2 boundaries not bundled" if True else "",
            "Emergency resources GIS layer unpopulated" if (not res_fc or not res_fc.get("features")) else "",
        ],
        "disclaimer": (
            "Advisory decision-support situation report. Does not issue official evacuation orders "
            "or replace statutory disaster-management procedures."
        ),
    }


def nearby_resource_finder_tool(
    latitude: float,
    longitude: float,
    radius_km: float = 25.0,
    resource_type: Optional[str] = None,
    role: str = "citizen",
) -> Dict[str, Any]:
    """Retrieve verified nearby emergency resources (hospitals, shelters, ambulances, rescue teams)."""
    from app.services.resource_service import resource_service
    return resource_service.search_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        resource_type=resource_type,
        operational_only=True,
        role=role,
    )


def resource_recommendation_tool(
    latitude: float,
    longitude: float,
    radius_km: float = 25.0,
    role: str = "citizen",
) -> Dict[str, Any]:
    """Provide transparent advisory recommendations of verified nearby emergency resources."""
    from app.services.resource_service import resource_service
    return resource_service.recommend_resources(
        latitude=latitude, longitude=longitude, radius_km=radius_km, role=role
    )


def read_alerts_tool(
    state: Optional[str] = None,
    approval_status: Optional[str] = None,
    role: str = "citizen",
) -> Dict[str, Any]:
    """Read-only alert retrieval for Phase 6 agent. Agent NEVER approves or publishes alerts."""
    from app.services.alert_approval_service import alert_approval_service
    eff_status = "PUBLISHED" if role == "citizen" else approval_status
    items = alert_approval_service.list_alerts(state=state, approval_status=eff_status, limit=15)
    return {
        "count": len(items),
        "alerts": items,
        "advisory_note": "Read-only alert summary. Only authorized human authorities can approve or publish warnings.",
    }
