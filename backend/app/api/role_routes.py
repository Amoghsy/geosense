import os
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status

from app.schemas.role_schema import (
    IncidentCreateRequest,
    IncidentVerifyRequest,
    IncidentAssignRequest,
    InspectionCreateRequest,
    InspectionUpdateRequest,
)
from app.schemas.agent_schema import SituationReportRequest
from app.services.auth_service import get_current_user, require_roles, log_audit_event
from app.services.weather_service import weather_service, make_location_id
from app.ml.landslide_weather_analyzer import analyze_rainfall
from app.ml.landslide_risk_engine import compute_dynamic_risk
from app.services.gis_service import gis_service
from app.services.resource_service import resource_service
from app.agent.tools import situation_report_tool
from app.db.database import get_db_connection, ensure_phase8_schema, get_latest_risk_by_location

router = APIRouter(tags=["Phase 8 — Multi-Role Workflows"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOADS_DIR = os.path.abspath(os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads")))


def _save_optional_photo(photo: Optional[UploadFile], prefix: str) -> Optional[str]:
    if not photo or not photo.filename:
        return None
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    ext = os.path.splitext(photo.filename)[1].lower() or ".jpg"
    fname = f"{prefix}_{uuid.uuid4().hex[:10]}{ext}"
    fpath = os.path.join(UPLOADS_DIR, fname)
    with open(fpath, "wb") as f:
        f.write(photo.file.read())
    return fname


# ==========================================
# PART A: CITIZEN ENDPOINTS
# ==========================================

@router.get("/citizen/risk", summary="Citizen Location Risk & Rainfall Summary")
async def citizen_risk(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    location_name: Optional[str] = Query(None),
):
    loc_id = make_location_id(latitude, longitude)
    bundle = await weather_service.fetch_weather_bundle(latitude, longitude, loc_id)
    rain = analyze_rainfall(bundle, persist=False)
    risk = compute_dynamic_risk(
        latitude=latitude,
        longitude=longitude,
        location_id=loc_id,
        location_name=location_name,
        weather_bundle=bundle,
        rainfall_analysis=rain,
        persist=True,
    )
    cat = "DATA UNAVAILABLE" if risk["risk_category"] == "INSUFFICIENT_DATA" else risk["risk_category"]
    return {
        "location_id": loc_id,
        "location_name": location_name,
        "latitude": latitude,
        "longitude": longitude,
        "risk_category": cat,
        "risk_score": risk["risk_score"],
        "assessment_time": risk["assessment_time"],
        "recent_rainfall_24h_mm": rain["observed_windows"]["24h"]["rainfall_mm"],
        "forecast_rainfall_24h_mm": rain["forecast_windows"]["next_24h"]["rainfall_mm"],
        "explanation": risk["explanation"],
        "disclaimer": "Decision-support indicator only; not a guarantee that a landslide will or will not occur.",
    }


@router.get("/citizen/resources/near", summary="Citizen Nearby Verified Public Resources")
async def citizen_nearby_resources(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(25.0, ge=1.0, le=100.0),
    resource_type: Optional[str] = Query(None),
):
    return resource_service.search_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        resource_type=resource_type,
        operational_only=True,
        role="citizen",
    )


@router.get("/citizen/dashboard", summary="Citizen Home Dashboard Data")
async def citizen_dashboard(
    latitude: float = Query(25.5788, ge=-90.0, le=90.0),
    longitude: float = Query(91.8933, ge=-180.0, le=180.0),
    location_name: Optional[str] = Query("Shillong, Meghalaya"),
    user: dict = Depends(get_current_user),
):
    risk_info = await citizen_risk(latitude=latitude, longitude=longitude, location_name=location_name)
    nearby_res = resource_service.search_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_km=25.0,
        operational_only=True,
        role="citizen",
    )
    ensure_phase8_schema()
    conn = get_db_connection()
    try:
        my_reports = [
            dict(r)
            for r in conn.execute(
                "SELECT id, incident_category, description, location_name, status, created_at FROM incidents WHERE reporter_user_id = ? ORDER BY created_at DESC LIMIT 5",
                (user["user_id"],),
            ).fetchall()
        ]
    finally:
        conn.close()

    return {
        "user": {"user_id": user["user_id"], "full_name": user["full_name"], "role": user["role"]},
        "risk": risk_info,
        "nearby_verified_resources": nearby_res["resources"][:5],
        "recent_reports": my_reports,
        "safety_guidance": [
            "Stay alert during intense or prolonged rainfall.",
            "Watch for slope cracks, leaning trees, or sudden muddy water in streams.",
            "Move away from steep unstable slopes and follow official NDMA/SDMA advisories.",
        ],
    }


@router.post("/incidents", status_code=status.HTTP_201_CREATED, summary="Submit Citizen/Officer Landslide Incident Report")
async def submit_incident(
    incident_category: str = Form("LANDSLIDE"),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    location_name: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    incident_time: Optional[str] = Form(None),
    contact_info: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user),
):
    ensure_phase8_schema()
    now_dt = datetime.now(timezone.utc)
    cutoff_iso = (now_dt - timedelta(seconds=60)).isoformat()

    conn = get_db_connection()
    try:
        # Prevent rapid duplicate submissions from same user at same coordinates
        dup = conn.execute(
            """
            SELECT id FROM incidents
            WHERE reporter_user_id = ? AND ABS(latitude - ?) < 0.001 AND ABS(longitude - ?) < 0.001
              AND created_at >= ?
            """,
            (user["user_id"], latitude, longitude, cutoff_iso),
        ).fetchone()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate incident submission detected (existing ID: {dup['id']}).",
            )

        photo_fname = _save_optional_photo(photo, "inc")
        inc_id = f"inc_{uuid.uuid4().hex[:12]}"
        now_iso = now_dt.isoformat()
        eff_state = state or gis_service._find_state_for_point(latitude, longitude)
        rep_type = "officer" if user["role"] in {"FIELD_OFFICER", "AUTHORITY", "ADMIN"} else "citizen"

        conn.execute(
            """
            INSERT INTO incidents (
                id, reporter_user_id, reporter_type, incident_category, status,
                latitude, longitude, description, location_name, state, district,
                photo_path, incident_time, contact_info, region_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inc_id, user["user_id"], rep_type, incident_category.upper(),
                latitude, longitude, description, location_name, eff_state, district,
                photo_fname, incident_time or now_iso, contact_info,
                (eff_state or "").lower().replace(" ", "_") or None, now_iso, now_iso,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "success": True,
        "incident_id": inc_id,
        "status": "PENDING",
        "message": "Incident report submitted and queued for official verification.",
        "created_at": now_iso,
    }


@router.get("/incidents/my-reports", summary="Retrieve Current User's Submitted Incident Reports")
async def get_my_reports(user: dict = Depends(get_current_user)):
    ensure_phase8_schema()
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM incidents WHERE reporter_user_id = ? ORDER BY created_at DESC",
            (user["user_id"],),
        ).fetchall()
        return {"count": len(rows), "incidents": [dict(r) for r in rows]}
    finally:
        conn.close()


# ==========================================
# PART B: FIELD OFFICER ENDPOINTS
# ==========================================

def _apply_officer_jurisdiction(user: dict, query_state: Optional[str]) -> Optional[str]:
    if user["role"] == "FIELD_OFFICER" and user.get("assigned_state"):
        if query_state and query_state.strip().lower() != user["assigned_state"].strip().lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cross-jurisdiction access denied. Assigned state: {user['assigned_state']}.",
            )
        return user["assigned_state"]
    return query_state


@router.get("/officer/incidents", summary="List Jurisdiction-Filtered Incident Reports (Officer/Authority)")
async def list_officer_incidents(
    state: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: dict = Depends(require_roles("FIELD_OFFICER", "AUTHORITY", "ADMIN")),
):
    eff_state = _apply_officer_jurisdiction(user, state)
    ensure_phase8_schema()
    clauses = []
    params: List[Any] = []
    if eff_state:
        clauses.append("LOWER(state) = ?")
        params.append(eff_state.strip().lower())
    if status_filter:
        clauses.append("status = ?")
        params.append(status_filter.upper())
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    conn = get_db_connection()
    try:
        rows = conn.execute(f"SELECT * FROM incidents {where_sql} ORDER BY created_at DESC LIMIT 100", tuple(params)).fetchall()
        return {"count": len(rows), "jurisdiction_state": eff_state, "incidents": [dict(r) for r in rows]}
    finally:
        conn.close()


@router.post("/incidents/{incident_id}/verify", summary="Verify or Reject Citizen Incident Report")
async def verify_incident(
    incident_id: str,
    req: IncidentVerifyRequest,
    user: dict = Depends(require_roles("FIELD_OFFICER", "AUTHORITY", "ADMIN")),
):
    ensure_phase8_schema()
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")
        inc = dict(row)
        if user["role"] == "FIELD_OFFICER" and user.get("assigned_state") and inc.get("state"):
            if inc["state"].strip().lower() != user["assigned_state"].strip().lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot verify incident outside your assigned jurisdiction.",
                )
        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            UPDATE incidents
            SET status = ?, verification_notes = ?, verified_by = ?, verified_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (req.status, req.verification_notes, user["user_id"], now_iso, now_iso, incident_id),
        )
        conn.commit()
    finally:
        conn.close()

    log_audit_event(
        user["user_id"], user["role"], f"INCIDENT_{req.status}", "incident", incident_id,
        {"notes": req.verification_notes},
    )
    return {"success": True, "incident_id": incident_id, "status": req.status, "verified_by": user["user_id"], "verified_at": now_iso}


@router.post("/inspections", status_code=status.HTTP_201_CREATED, summary="Submit Field Inspection Report")
async def create_inspection(
    latitude: float = Form(...),
    longitude: float = Form(...),
    observations: str = Form(...),
    location_id: Optional[str] = Form(None),
    location_name: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    inspection_status: str = Form("IN_PROGRESS", alias="status"),
    inspection_notes: Optional[str] = Form(None),
    follow_up_required: bool = Form(False),
    photo: Optional[UploadFile] = File(None),
    user: dict = Depends(require_roles("FIELD_OFFICER", "AUTHORITY", "ADMIN")),
):
    eff_state = state or gis_service._find_state_for_point(latitude, longitude)
    if user["role"] == "FIELD_OFFICER" and user.get("assigned_state") and eff_state:
        if eff_state.strip().lower() != user["assigned_state"].strip().lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inspection outside assigned jurisdiction.")

    ensure_phase8_schema()
    loc_id = location_id or make_location_id(latitude, longitude)
    latest_risk = get_latest_risk_by_location(loc_id)
    photo_fname = _save_optional_photo(photo, "insp")
    insp_id = f"insp_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO field_inspections (
                inspection_id, officer_id, location_id, latitude, longitude,
                location_name, state, district, status, observations, inspection_notes,
                photo_path, follow_up_required, risk_score_snapshot, risk_category_snapshot,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                insp_id, user["user_id"], loc_id, latitude, longitude,
                location_name, eff_state, district, inspection_status.upper(),
                observations, inspection_notes, photo_fname, 1 if follow_up_required else 0,
                latest_risk.get("risk_score") if latest_risk else None,
                latest_risk.get("risk_category") if latest_risk else None,
                now_iso, now_iso,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    log_audit_event(user["user_id"], user["role"], "INSPECTION_CREATED", "inspection", insp_id, {"location_id": loc_id})
    return {"success": True, "inspection_id": insp_id, "status": inspection_status.upper(), "created_at": now_iso}


@router.get("/inspections", summary="List Field Inspections")
async def list_inspections(
    state: Optional[str] = Query(None),
    user: dict = Depends(require_roles("FIELD_OFFICER", "AUTHORITY", "ADMIN")),
):
    eff_state = _apply_officer_jurisdiction(user, state)
    ensure_phase8_schema()
    conn = get_db_connection()
    try:
        if eff_state:
            rows = conn.execute(
                "SELECT * FROM field_inspections WHERE LOWER(state) = ? ORDER BY created_at DESC LIMIT 100",
                (eff_state.strip().lower(),),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM field_inspections ORDER BY created_at DESC LIMIT 100").fetchall()
        return {"count": len(rows), "inspections": [dict(r) for r in rows]}
    finally:
        conn.close()


@router.patch("/inspections/{inspection_id}", summary="Update Field Inspection Status or Notes")
async def update_inspection(
    inspection_id: str,
    req: InspectionUpdateRequest,
    user: dict = Depends(require_roles("FIELD_OFFICER", "AUTHORITY", "ADMIN")),
):
    ensure_phase8_schema()
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM field_inspections WHERE inspection_id = ?", (inspection_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found.")
        sets = []
        params: List[Any] = []
        if req.status is not None:
            sets.append("status = ?")
            params.append(req.status)
        if req.observations is not None:
            sets.append("observations = ?")
            params.append(req.observations)
        if req.inspection_notes is not None:
            sets.append("inspection_notes = ?")
            params.append(req.inspection_notes)
        if req.follow_up_required is not None:
            sets.append("follow_up_required = ?")
            params.append(1 if req.follow_up_required else 0)
        now_iso = datetime.now(timezone.utc).isoformat()
        sets.append("updated_at = ?")
        params.append(now_iso)
        params.append(inspection_id)
        conn.execute(f"UPDATE field_inspections SET {', '.join(sets)} WHERE inspection_id = ?", tuple(params))
        conn.commit()
        updated = dict(conn.execute("SELECT * FROM field_inspections WHERE inspection_id = ?", (inspection_id,)).fetchone())
    finally:
        conn.close()

    log_audit_event(user["user_id"], user["role"], "INSPECTION_UPDATED", "inspection", inspection_id, {"status": req.status})
    return updated


@router.get("/officer/assignments", summary="Get Assigned Incidents & Priority Locations for Officer")
async def officer_assignments(user: dict = Depends(require_roles("FIELD_OFFICER", "AUTHORITY", "ADMIN"))):
    ensure_phase8_schema()
    eff_state = user.get("assigned_state")
    conn = get_db_connection()
    try:
        assigned_inc = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM incidents WHERE assigned_officer_id = ? ORDER BY created_at DESC",
                (user["user_id"],),
            ).fetchall()
        ]
    finally:
        conn.close()
    hotspots = gis_service.get_hotspots(state=eff_state, limit=10)
    return {
        "officer_id": user["user_id"],
        "assigned_state": eff_state,
        "assigned_incidents": assigned_inc,
        "priority_hotspots": hotspots.get("hotspots", []),
    }


@router.get("/officer/dashboard", summary="Field Officer Operational Dashboard")
async def officer_dashboard(user: dict = Depends(require_roles("FIELD_OFFICER", "AUTHORITY", "ADMIN"))):
    eff_state = user.get("assigned_state")
    inc_data = await list_officer_incidents(state=eff_state, status_filter=None, user=user)
    insp_data = await list_inspections(state=eff_state, user=user)
    assign_data = await officer_assignments(user=user)
    sat_fc = gis_service.get_layer_features("phase1_detections", region=eff_state, limit=10)
    return {
        "officer": {"user_id": user["user_id"], "full_name": user["full_name"], "assigned_state": eff_state, "assigned_district": user.get("assigned_district")},
        "pending_incidents_count": sum(1 for i in inc_data["incidents"] if i["status"] == "PENDING"),
        "incidents": inc_data["incidents"][:10],
        "inspections": insp_data["inspections"][:10],
        "priority_hotspots": assign_data["priority_hotspots"],
        "satellite_detections": sat_fc.get("features", []) if sat_fc else [],
    }


# ==========================================
# PART C: AUTHORITY ENDPOINTS
# ==========================================

@router.get("/authority/dashboard", summary="Disaster Management Authority Overview Dashboard")
async def authority_dashboard(user: dict = Depends(require_roles("AUTHORITY", "ADMIN"))):
    ensure_phase8_schema()
    gis_sum = gis_service.get_summary()
    res_stats = resource_service.get_statistics(role="authority")
    hotspots = gis_service.get_hotspots(limit=25)
    conn = get_db_connection()
    try:
        inc_rows = [dict(r) for r in conn.execute("SELECT * FROM incidents ORDER BY created_at DESC LIMIT 50").fetchall()]
        insp_rows = [dict(r) for r in conn.execute("SELECT * FROM field_inspections ORDER BY created_at DESC LIMIT 50").fetchall()]
    finally:
        conn.close()

    return {
        "authority_user": {"user_id": user["user_id"], "full_name": user["full_name"], "role": user["role"]},
        "gis_summary": gis_sum,
        "resource_statistics": res_stats,
        "hotspots": hotspots.get("hotspots", []),
        "incidents_summary": {
            "total": len(inc_rows),
            "pending": sum(1 for i in inc_rows if i["status"] == "PENDING"),
            "verified": sum(1 for i in inc_rows if i["status"] == "VERIFIED"),
            "recent": inc_rows[:10],
        },
        "inspections_summary": {
            "total": len(insp_rows),
            "completed": sum(1 for i in insp_rows if i["status"] == "COMPLETED"),
            "recent": insp_rows[:10],
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/authority/analytics", summary="State-wise Risk Distribution Analytics")
async def authority_analytics(user: dict = Depends(require_roles("AUTHORITY", "ADMIN"))):
    feats = gis_service._get_phase3_risk_features("risk")
    by_state: Dict[str, Dict[str, int]] = {}
    for f in feats:
        p = f["properties"]
        st = p.get("region") or "Unassigned"
        cat = p.get("risk_category") or "UNKNOWN"
        if st not in by_state:
            by_state[st] = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0, "INSUFFICIENT_DATA": 0}
        by_state[st][cat] = by_state[st].get(cat, 0) + 1
    return {"total_locations": len(feats), "state_distribution": by_state}


@router.get("/authority/incidents", summary="Authority Incident Management List")
async def authority_incidents(
    state: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: dict = Depends(require_roles("AUTHORITY", "ADMIN")),
):
    return await list_officer_incidents(state=state, status_filter=status_filter, user=user)


@router.post("/authority/incidents/{incident_id}/assign", summary="Assign Incident to Field Officer")
async def assign_incident(
    incident_id: str,
    req: IncidentAssignRequest,
    user: dict = Depends(require_roles("AUTHORITY", "ADMIN")),
):
    ensure_phase8_schema()
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT id FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
        conn.execute(
            "UPDATE incidents SET assigned_officer_id = ?, updated_at = ? WHERE id = ?",
            (req.officer_id, now_iso, incident_id),
        )
        conn.commit()
    finally:
        conn.close()
    log_audit_event(user["user_id"], user["role"], "INCIDENT_ASSIGNED", "incident", incident_id, {"officer_id": req.officer_id, "notes": req.notes})
    return {"success": True, "incident_id": incident_id, "assigned_officer_id": req.officer_id}


@router.get("/authority/audit-logs", summary="Retrieve Administrative Audit Logs")
async def get_audit_logs(limit: int = Query(50, ge=1, le=200), user: dict = Depends(require_roles("AUTHORITY", "ADMIN"))):
    ensure_phase8_schema()
    conn = get_db_connection()
    try:
        rows = [dict(r) for r in conn.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()]
        return {"count": len(rows), "logs": rows}
    finally:
        conn.close()


@router.post("/authority/situation-reports", summary="Generate & Persist Authority Situation Report")
async def create_authority_situation_report(
    req: SituationReportRequest,
    user: dict = Depends(require_roles("AUTHORITY", "ADMIN")),
):
    ensure_phase8_schema()
    report = await situation_report_tool(
        region_id=req.region_id, latitude=req.latitude, longitude=req.longitude, role="authority"
    )
    rep_id = f"rep_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    report["report_id"] = rep_id

    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO situation_reports (report_id, generated_by, actor_role, region_id, report_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (rep_id, user["user_id"], user["role"], req.region_id, json.dumps(report), now_iso),
        )
        conn.commit()
    finally:
        conn.close()

    log_audit_event(user["user_id"], user["role"], "SITUATION_REPORT_GENERATED", "situation_report", rep_id, {"region_id": req.region_id})
    return report


@router.get("/authority/situation-reports", summary="List Stored Authority Situation Reports")
async def list_authority_situation_reports(user: dict = Depends(require_roles("AUTHORITY", "ADMIN"))):
    ensure_phase8_schema()
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT report_id, generated_by, region_id, created_at, report_json FROM situation_reports ORDER BY created_at DESC LIMIT 25").fetchall()
        return {
            "count": len(rows),
            "reports": [
                {
                    "report_id": r["report_id"],
                    "generated_by": r["generated_by"],
                    "region_id": r["region_id"],
                    "created_at": r["created_at"],
                    "report": json.loads(r["report_json"]),
                }
                for r in rows
            ],
        }
    finally:
        conn.close()
