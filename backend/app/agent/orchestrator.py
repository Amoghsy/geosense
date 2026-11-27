import os
import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

from app.agent.tools import (
    weather_analysis_tool,
    landslide_risk_analysis_tool,
    satellite_detection_tool,
    susceptibility_analysis_tool,
    gis_location_tool,
    risk_explanation_tool,
    historical_trend_tool,
    hotspot_prioritization_tool,
    situation_report_tool,
    nearby_resource_finder_tool,
    resource_recommendation_tool,
)
from app.services.weather_service import make_location_id
from app.db.database import (
    create_agent_session,
    get_agent_session,
    update_agent_session,
)

logger = logging.getLogger("geosense.agent.orchestrator")

# Check Google ADK & Gemini availability
try:
    from google.adk.agents import Agent as ADKAgent  # type: ignore
    GOOGLE_ADK_AVAILABLE = True
except Exception:
    ADKAgent = None
    GOOGLE_ADK_AVAILABLE = False

NE_PLACE_COORDS: Dict[str, Tuple[float, float, str, str]] = {
    "shillong": (25.5788, 91.8933, "Shillong, Meghalaya", "Meghalaya"),
    "meghalaya": (25.5788, 91.8933, "Shillong, Meghalaya", "Meghalaya"),
    "gangtok": (27.3389, 88.6065, "Gangtok, Sikkim", "Sikkim"),
    "sikkim": (27.3389, 88.6065, "Gangtok, Sikkim", "Sikkim"),
    "guwahati": (26.1445, 91.7362, "Guwahati, Assam", "Assam"),
    "assam": (26.1445, 91.7362, "Guwahati, Assam", "Assam"),
    "itanagar": (27.0844, 93.6053, "Itanagar, Arunachal Pradesh", "Arunachal Pradesh"),
    "arunachal": (27.0844, 93.6053, "Itanagar, Arunachal Pradesh", "Arunachal Pradesh"),
    "imphal": (24.8170, 93.9368, "Imphal, Manipur", "Manipur"),
    "manipur": (24.8170, 93.9368, "Imphal, Manipur", "Manipur"),
    "aizawl": (23.7271, 92.7176, "Aizawl, Mizoram", "Mizoram"),
    "mizoram": (23.7271, 92.7176, "Aizawl, Mizoram", "Mizoram"),
    "kohima": (25.6751, 94.1086, "Kohima, Nagaland", "Nagaland"),
    "nagaland": (25.6751, 94.1086, "Kohima, Nagaland", "Nagaland"),
    "agartala": (23.8315, 91.2868, "Agartala, Tripura", "Tripura"),
    "tripura": (23.8315, 91.2868, "Agartala, Tripura", "Tripura"),
}


def has_gemini_api_key() -> bool:
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def build_adk_agent_definition():
    """Build Google ADK Agent instance wired with GeoSense backend tools."""
    if not GOOGLE_ADK_AVAILABLE:
        return None
    return ADKAgent(
        name="geosense_orchestrator",
        model=os.getenv("GEOSENSE_ADK_MODEL", "gemini-2.5-flash"),
        description="GeoSense AI Decision-Support Orchestrator for North Eastern India landslide monitoring.",
        instruction=(
            "You are the GeoSense Decision-Support Assistant. Always call GeoSense tools to retrieve "
            "real data. Never invent rainfall, risk scores, or detections. Never call the risk index "
            "a probability. Clearly separate observed from forecast rainfall, state missing data, "
            "and respect user roles (citizen, field_officer, authority)."
        ),
        tools=[
            weather_analysis_tool,
            landslide_risk_analysis_tool,
            satellite_detection_tool,
            susceptibility_analysis_tool,
            gis_location_tool,
            risk_explanation_tool,
            historical_trend_tool,
            hotspot_prioritization_tool,
            situation_report_tool,
        ],
    )


def _resolve_location_from_text_or_ctx(
    message: str,
    req_ctx: Dict[str, Any],
    sess_ctx: Dict[str, Any],
) -> Dict[str, Any]:
    ctx = dict(sess_ctx)
    for k, v in req_ctx.items():
        if v is not None:
            ctx[k] = v

    # Check explicit lat/lon pair in message
    coord_match = re.search(r"(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)", message)
    if coord_match:
        lat = float(coord_match.group(1))
        lon = float(coord_match.group(2))
        ctx["latitude"] = lat
        ctx["longitude"] = lon
        ctx["location_id"] = make_location_id(lat, lon)
        return ctx

    msg_l = message.lower()
    for key, (lat, lon, label, state) in NE_PLACE_COORDS.items():
        if key in msg_l:
            ctx["latitude"] = lat
            ctx["longitude"] = lon
            ctx["location_name"] = label
            ctx["region_id"] = state.lower().replace(" ", "_")
            ctx["state"] = state
            ctx["location_id"] = make_location_id(lat, lon)
            return ctx

    if ctx.get("latitude") is not None and ctx.get("longitude") is not None and not ctx.get("location_id"):
        ctx["location_id"] = make_location_id(float(ctx["latitude"]), float(ctx["longitude"]))
    return ctx


class GeoSenseOrchestrator:
    """
    Phase 6 Orchestrator:
    - Uses Google ADK when GEMINI_API_KEY/GOOGLE_API_KEY is configured.
    - Uses Grounded Deterministic Tool-Router when running without an external LLM key,
      guaranteeing real tool execution, session memory, and strict role-based controls.
    """

    def __init__(self):
        self.adk_agent = build_adk_agent_definition()

    def get_health_info(self) -> Dict[str, Any]:
        key_ok = has_gemini_api_key()
        mode = "google_adk" if (GOOGLE_ADK_AVAILABLE and key_ok) else "deterministic_tool_router"
        return {
            "status": "healthy",
            "google_adk_installed": GOOGLE_ADK_AVAILABLE,
            "gemini_api_key_configured": key_ok,
            "active_execution_mode": mode,
            "available_tools": [
                "weather_analysis_tool",
                "landslide_risk_analysis_tool",
                "satellite_detection_tool",
                "susceptibility_analysis_tool",
                "gis_location_tool",
                "risk_explanation_tool",
                "historical_trend_tool",
                "hotspot_prioritization_tool",
                "situation_report_tool",
            ],
        }

    def start_session(
        self,
        role: str = "citizen",
        user_id: Optional[str] = None,
        location_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        sid = f"sess_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        sess = {
            "session_id": sid,
            "user_role": role,
            "user_id": user_id,
            "location_context": location_context or {},
            "messages": [],
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        create_agent_session(sess)
        return {
            "session_id": sid,
            "role": role,
            "user_id": user_id,
            "location_context": sess["location_context"],
            "messages": [],
            "created_at": now_iso,
            "updated_at": now_iso,
        }

    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        role: str = "citizen",
        user_id: Optional[str] = None,
        location_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Load or create session with role isolation
        if session_id:
            sess = get_agent_session(session_id)
            if not sess:
                raise KeyError(f"Session '{session_id}' not found or expired.")
            if sess["user_role"] != role:
                raise PermissionError(
                    f"Role mismatch: session belongs to '{sess['user_role']}', not '{role}'."
                )
            if sess.get("user_id") and user_id and sess["user_id"] != user_id:
                raise PermissionError("Unauthorized access to another user's session.")
        else:
            created = self.start_session(role=role, user_id=user_id, location_context=location_context)
            sess = get_agent_session(created["session_id"])

        sid = sess["session_id"]
        ctx = _resolve_location_from_text_or_ctx(message, location_context or {}, sess.get("location_context", {}))
        msg_l = message.lower()

        tools_used: List[str] = []
        sources: List[str] = []
        timestamps: Dict[str, Any] = {}
        structured_data: Dict[str, Any] = {}
        warnings: List[str] = []
        reply_parts: List[str] = []

        lat = ctx.get("latitude")
        lon = ctx.get("longitude")
        loc_id = ctx.get("location_id")
        loc_name = ctx.get("location_name") or (f"({lat}, {lon})" if lat is not None else "North Eastern India")
        state = ctx.get("state")

        # Intent classification & grounded tool execution
        wants_situation = any(w in msg_l for w in ("situation report", "briefing", "district summary"))
        wants_hotspots = any(w in msg_l for w in ("hotspot", "inspect first", "elevated risk", "priority", "which areas"))
        wants_trend = any(w in msg_l for w in ("trend", "increased", "decreased", "last 7", "seven days", "history", "changed"))
        wants_explain = any(w in msg_l for w in ("why", "factor", "cause", "explain", "contribut"))
        wants_weather = any(w in msg_l for w in ("rain", "weather", "forecast", "awi", "wetness", "storm"))
        wants_sat = any(w in msg_l for w in ("satellite", "prithvi", "detection", "mask"))
        wants_susc = any(w in msg_l for w in ("susceptib", "multimodal", "phase 2"))
        wants_res = any(w in msg_l for w in ("hospital", "shelter", "ambulance", "rescue", "resource", "relief", "fire station", "police"))

        # Default to risk + weather if general risk question
        wants_risk = any(w in msg_l for w in ("risk", "safe", "status", "current")) or not (
            wants_situation or wants_hotspots or wants_sat or wants_susc or wants_res
        )

        # 1. Situation Report (Role-restricted)
        if wants_situation:
            tools_used.append("situation_report_tool")
            sr = await situation_report_tool(region_id=ctx.get("region_id"), latitude=lat, longitude=lon, role=role)
            if not sr.get("authorized"):
                reply_parts.append(sr["message"])
            else:
                structured_data["situation_report"] = sr
                sources.append("GeoSense GIS & Phase 1-3 Stores")
                timestamps["report_generated_at"] = sr["report_generated_at"]
                reply_parts.append(
                    f"Situation Report ({sr['region']}, generated {sr['report_generated_at'][:19]}Z): "
                    f"{sr['gis_summary']['total_risk_assessments']} assessed locations, "
                    f"{sr['gis_summary']['high_risk_locations']} HIGH and {sr['gis_summary']['critical_risk_locations']} CRITICAL. "
                    f"{sr['disclaimer']}"
                )

        # 2. Hotspots / Inspection Priorities
        if wants_hotspots:
            if role in {"field_officer", "authority"}:
                tools_used.append("hotspot_prioritization_tool")
                hp = hotspot_prioritization_tool(state=state, role=role)
                structured_data["hotspots"] = hp.get("priorities", [])
                sources.append("GeoSense Phase 3/4 Hotspots")
                if hp.get("priorities"):
                    top = hp["priorities"][0]
                    reply_parts.append(
                        f"Top priority hotspot: {top.get('location_name') or top['location_id']} "
                        f"({top['risk_category']}, {top['risk_score']}/100). {hp['advisory_note']}"
                    )
                else:
                    reply_parts.append("No HIGH or CRITICAL hotspots are currently recorded in the database for this area.")
            else:
                tools_used.append("gis_location_tool")
                gl = gis_location_tool(latitude=lat, longitude=lon, state=state, role="citizen")
                hs = gl.get("hotspots", {}).get("hotspots", [])
                structured_data["hotspots"] = hs
                reply_parts.append(
                    f"Public hotspot summary: {len(hs)} elevated-risk location(s) recorded. "
                    "Please follow official disaster-management advisories and avoid steep slopes during heavy rain."
                )

        # 3. Location Risk & Explanation
        if (wants_risk or wants_explain) and lat is not None and lon is not None:
            tools_used.append("landslide_risk_analysis_tool")
            r_res = await landslide_risk_analysis_tool(lat, lon, loc_id, loc_name)
            assess = r_res["assessment"]
            ctx["last_assessment_id"] = assess["assessment_id"]
            structured_data["risk_summary"] = {
                "assessment_id": assess["assessment_id"],
                "risk_score": assess.get("risk_score"),
                "risk_category": assess.get("risk_category"),
                "completeness_score": assess.get("completeness_score"),
                "assessment_time": assess.get("assessment_time"),
            }
            sources.extend(assess.get("data_sources", []))
            timestamps["assessment_time"] = assess.get("assessment_time")
            warnings.extend(assess.get("warnings", []))

            if wants_explain:
                tools_used.append("risk_explanation_tool")
                exp = risk_explanation_tool(assess["assessment_id"])
                if exp.get("available"):
                    e_obj = exp["explanation"]
                    structured_data["factor_contributions"] = e_obj["factor_contributions"]
                    reply_parts.append(e_obj["explanation"])
            else:
                reply_parts.append(
                    f"For {loc_name}, the current heuristic landslide risk is {assess['risk_category']} "
                    f"(index {assess['risk_score']}/100, completeness {round(assess['completeness_score']*100)}%, "
                    f"assessed {assess['assessment_time'][:19]}Z; not a calibrated probability)."
                )
        elif (wants_risk or wants_explain) and lat is None:
            reply_parts.append(
                "Please specify a North Eastern India location (e.g., Shillong, Gangtok, Guwahati, Itanagar) "
                "or coordinates (lat, lon) so I can retrieve real risk and weather records."
            )

        # 4. Weather & Rainfall
        if wants_weather and lat is not None and lon is not None:
            tools_used.append("weather_analysis_tool")
            wx = await weather_analysis_tool(lat, lon, loc_id)
            structured_data["rainfall_summary"] = {
                "observed_mm": wx["observed_rainfall_mm"],
                "forecast_mm": wx["forecast_rainfall_mm"],
                "awi_proxy": wx["awi_proxy"],
                "heavy_rainfall_detected": wx["heavy_rainfall_detected"],
            }
            sources.extend(wx["sources"])
            timestamps["weather_observation_time"] = wx["observation_time"]
            reply_parts.append(
                f"Weather for {loc_name} (observed {wx['observation_time']}): "
                f"24h observed rainfall is {wx['observed_rainfall_mm']['24h']} mm, "
                f"72h observed is {wx['observed_rainfall_mm']['72h']} mm, "
                f"AWI wetness proxy is {wx['awi_proxy']['awi_value']} mm (not measured soil moisture). "
                f"Forecast next 24h: {wx['forecast_rainfall_mm']['next_24h']} mm."
            )

        # 5. Historical Trends
        if wants_trend and loc_id:
            tools_used.append("historical_trend_tool")
            tr = historical_trend_tool(loc_id)
            structured_data["trend_summary"] = tr
            reply_parts.append(tr["message"])

        # 6. Satellite Detection (Phase 1)
        if wants_sat:
            tools_used.append("satellite_detection_tool")
            sat = satellite_detection_tool(latitude=lat, longitude=lon, role=role)
            structured_data["satellite_detection"] = sat
            if sat.get("available"):
                reply_parts.append(f"Phase 1 Prithvi satellite evidence found ({sat.get('count', len(sat.get('detections', [])))} feature(s)).")
            else:
                reply_parts.append(sat["message"])

        # 7. Susceptibility (Phase 2)
        if wants_susc:
            tools_used.append("susceptibility_analysis_tool")
            susc = susceptibility_analysis_tool(region=ctx.get("region_id"))
            structured_data["susceptibility"] = susc
            reply_parts.append(
                susc.get("coverage_disclaimer") or susc.get("message")
            )

        # 8. Emergency Resources (Phase 7)
        if wants_res and lat is not None and lon is not None:
            tools_used.append("nearby_resource_finder_tool")
            rtype = None
            if "hospital" in msg_l:
                rtype = "HOSPITAL"
            elif "shelter" in msg_l:
                rtype = "SHELTER"
            elif "ambulance" in msg_l:
                rtype = "AMBULANCE"
            elif "rescue" in msg_l:
                rtype = "RESCUE_TEAM"
            res_out = nearby_resource_finder_tool(lat, lon, radius_km=25.0, resource_type=rtype, role=role)
            structured_data["nearby_resources"] = res_out
            sources.append("GeoSense Verified Emergency Resources")
            if res_out["count"] > 0:
                top_r = res_out["resources"][0]
                reply_parts.append(
                    f"Found {res_out['count']} verified resource(s) within 25 km (straight-line distance). "
                    f"Nearest: {top_r['resource_name']} ({top_r['resource_type']}, {top_r['distance_km']} km straight-line, "
                    f"operational: {top_r['operational_status']}, availability: {top_r['availability_status']})."
                )
            else:
                reply_parts.append(
                    f"No verified {rtype or 'emergency'} resources are currently registered within 25 km of {loc_name}."
                )

        # Role-based safety note for Citizens
        if role == "citizen":
            reply_parts.append(
                "Safety note: This is advisory decision-support, not an official evacuation order. "
                "Follow local NDMA/SDMA authorities during heavy rainfall."
            )

        final_reply = " ".join(p for p in reply_parts if p)
        now_iso = datetime.now(timezone.utc).isoformat()
        messages = list(sess.get("messages", []))
        messages.append({"role": "user", "content": message, "timestamp": now_iso})
        messages.append({"role": "assistant", "content": final_reply, "tools_used": tools_used, "timestamp": now_iso})
        update_agent_session(sid, ctx, messages, now_iso)

        mode = "google_adk" if (GOOGLE_ADK_AVAILABLE and has_gemini_api_key()) else "deterministic_tool_router"
        return {
            "success": True,
            "session_id": sid,
            "role": role,
            "execution_mode": mode,
            "reply": final_reply,
            "tools_used": list(dict.fromkeys(tools_used)),
            "source_references": list(dict.fromkeys(sources)),
            "timestamps": timestamps,
            "location_context": ctx,
            "structured_data": structured_data,
            "warnings": list(dict.fromkeys(warnings)),
        }


agent_orchestrator = GeoSenseOrchestrator()
