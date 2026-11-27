import math
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import httpx

from app.db.database import get_db_connection, ensure_phase7_resource_schema
from app.gis.geo_utils import validate_coordinates

logger = logging.getLogger("geosense.resource_service")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle straight-line geographic distance in kilometres (NOT road distance)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return round(2.0 * r * math.asin(math.sqrt(a)), 3)


def _row_to_resource(row: Any, role: str = "citizen", distance_km: Optional[float] = None) -> Dict[str, Any]:
    d = dict(row)
    cap = d.get("capacity")
    occ = d.get("current_occupancy")
    rem = (cap - occ) if (cap is not None and occ is not None and cap >= occ) else None

    is_public = bool(d.get("is_public_contact", 0))
    contact = d.get("contact_number")
    if role == "citizen" and contact and not is_public:
        contact = "[Restricted — Authority/Officer Only]"

    return {
        "resource_id": d["id"],
        "resource_name": d.get("resource_name") or d.get("name") or "Unnamed Resource",
        "resource_type": d["resource_type"],
        "description": d.get("description"),
        "address": d.get("address"),
        "state": d.get("state"),
        "district": d.get("district"),
        "latitude": d["latitude"],
        "longitude": d["longitude"],
        "contact_number": contact,
        "is_public_contact": is_public,
        "capacity": cap,
        "current_occupancy": occ,
        "remaining_capacity": rem,
        "availability_status": d.get("availability_status") or "UNKNOWN",
        "operational_status": d.get("operational_status") or "UNKNOWN",
        "verification_status": d.get("verification_status") or "PENDING",
        "source": d.get("source") or "Manual Registration",
        "last_verified_at": d.get("last_verified_at"),
        "created_at": d["created_at"],
        "updated_at": d.get("updated_at"),
        "distance_km": distance_km,
        "distance_note": "Straight-line geographic distance (not road travel distance)" if distance_km is not None else None,
    }


def _record_history(
    resource_id: str,
    action: str,
    actor_role: str,
    actor_id: Optional[str],
    prev_state: Optional[Dict[str, Any]],
    new_state: Dict[str, Any],
    notes: Optional[str] = None,
) -> None:
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO resource_history (
                history_id, resource_id, action, actor_role, actor_id,
                previous_state_json, new_state_json, notes, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"rhist_{uuid.uuid4().hex[:12]}",
                resource_id,
                action,
                actor_role,
                actor_id,
                json.dumps(prev_state) if prev_state else None,
                json.dumps(new_state),
                notes,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


class ResourceService:
    def __init__(self):
        ensure_phase7_resource_schema()

    def create_resource(
        self,
        data: Dict[str, Any],
        actor_role: str = "field_officer",
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if actor_role == "citizen":
            raise PermissionError("Citizens cannot register emergency facilities directly.")
        validate_coordinates(data["latitude"], data["longitude"])
        ensure_phase7_resource_schema()

        rid = f"res_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        region_id = (data.get("state") or "").lower().replace(" ", "_") or None

        conn = get_db_connection()
        try:
            # Never auto-mark operational or verified on creation
            conn.execute(
                """
                INSERT INTO emergency_resources (
                    id, resource_type, name, resource_name, description, address,
                    state, district, latitude, longitude, region_id,
                    contact_number, is_public_contact, capacity, current_occupancy,
                    availability_status, operational_status, verification_status,
                    source, last_verified_at, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rid,
                    data["resource_type"],
                    data["resource_name"],
                    data["resource_name"],
                    data.get("description"),
                    data.get("address"),
                    data.get("state"),
                    data.get("district"),
                    data["latitude"],
                    data["longitude"],
                    region_id,
                    data.get("contact_number"),
                    1 if data.get("is_public_contact") else 0,
                    data.get("capacity"),
                    data.get("current_occupancy"),
                    "UNKNOWN",
                    "UNKNOWN",
                    "PENDING",
                    data.get("source") or "Authority / Field Submission",
                    None,
                    json.dumps({}),
                    now_iso,
                    now_iso,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        created = self.get_resource(rid, role=actor_role)
        _record_history(rid, "CREATED", actor_role, actor_id, None, created, "Initial registration (PENDING verification)")
        return created

    def get_resource(self, resource_id: str, role: str = "citizen") -> Optional[Dict[str, Any]]:
        ensure_phase7_resource_schema()
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT * FROM emergency_resources WHERE id = ?", (resource_id,)).fetchone()
            if not row:
                return None
            res = _row_to_resource(row, role=role)
            if role == "citizen" and res["verification_status"] != "VERIFIED":
                return None
            return res
        finally:
            conn.close()

    def list_resources(
        self,
        role: str = "citizen",
        resource_type: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        verification_status: Optional[str] = None,
        operational_status: Optional[str] = None,
        availability_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        ensure_phase7_resource_schema()
        clauses: List[str] = []
        params: List[Any] = []

        if role == "citizen":
            clauses.append("verification_status = 'VERIFIED'")
        elif verification_status:
            clauses.append("verification_status = ?")
            params.append(verification_status.upper())

        if resource_type:
            clauses.append("resource_type = ?")
            params.append(resource_type.upper())
        if state:
            clauses.append("LOWER(state) = ?")
            params.append(state.strip().lower())
        if district:
            clauses.append("LOWER(district) = ?")
            params.append(district.strip().lower())
        if operational_status:
            clauses.append("operational_status = ?")
            params.append(operational_status.upper())
        if availability_status:
            clauses.append("availability_status = ?")
            params.append(availability_status.upper())

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        conn = get_db_connection()
        try:
            total = conn.execute(f"SELECT COUNT(*) AS cnt FROM emergency_resources {where_sql}", tuple(params)).fetchone()["cnt"]
            rows = conn.execute(
                f"SELECT * FROM emergency_resources {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                tuple(params + [limit, offset]),
            ).fetchall()
            items = [_row_to_resource(r, role=role) for r in rows]
            return {"count": len(items), "total_matched": total, "resources": items}
        finally:
            conn.close()

    def update_resource(
        self,
        resource_id: str,
        updates: Dict[str, Any],
        actor_role: str = "authority",
        actor_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if actor_role not in {"field_officer", "authority"}:
            raise PermissionError("Only Field Officers or Authorities may edit resource details.")
        prev = self.get_resource(resource_id, role=actor_role)
        if not prev:
            return None

        if "latitude" in updates and "longitude" in updates and updates["latitude"] is not None and updates["longitude"] is not None:
            validate_coordinates(updates["latitude"], updates["longitude"])

        allowed_cols = {
            "resource_name", "resource_type", "description", "address",
            "state", "district", "latitude", "longitude", "contact_number",
            "is_public_contact", "capacity", "current_occupancy",
        }
        sets: List[str] = []
        params: List[Any] = []
        for k, v in updates.items():
            if k in allowed_cols and v is not None:
                if k == "is_public_contact":
                    v = 1 if v else 0
                sets.append(f"{k} = ?")
                params.append(v)
                if k == "resource_name":
                    sets.append("name = ?")
                    params.append(v)

        if not sets:
            return prev

        now_iso = datetime.now(timezone.utc).isoformat()
        sets.append("updated_at = ?")
        params.append(now_iso)
        params.append(resource_id)

        conn = get_db_connection()
        try:
            conn.execute(f"UPDATE emergency_resources SET {', '.join(sets)} WHERE id = ?", tuple(params))
            conn.commit()
        finally:
            conn.close()

        updated = self.get_resource(resource_id, role=actor_role)
        _record_history(resource_id, "UPDATED", actor_role, actor_id, prev, updated, "Resource details updated")
        return updated

    def verify_resource(
        self,
        resource_id: str,
        verification_status: str,
        operational_status: Optional[str] = None,
        availability_status: Optional[str] = None,
        notes: Optional[str] = None,
        actor_role: str = "authority",
        actor_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if actor_role != "authority":
            raise PermissionError("Only Disaster Management Authorities can verify or reject resources.")
        prev = self.get_resource(resource_id, role=actor_role)
        if not prev:
            return None

        now_iso = datetime.now(timezone.utc).isoformat()
        eff_op = operational_status or prev["operational_status"]
        eff_avail = availability_status or prev["availability_status"]
        last_ver = now_iso if verification_status == "VERIFIED" else prev.get("last_verified_at")

        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE emergency_resources
                SET verification_status = ?, operational_status = ?, availability_status = ?,
                    last_verified_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (verification_status, eff_op, eff_avail, last_ver, now_iso, resource_id),
            )
            conn.commit()
        finally:
            conn.close()

        updated = self.get_resource(resource_id, role=actor_role)
        _record_history(resource_id, f"VERIFICATION_{verification_status}", actor_role, actor_id, prev, updated, notes)
        return updated

    def update_availability(
        self,
        resource_id: str,
        operational_status: Optional[str] = None,
        availability_status: Optional[str] = None,
        capacity: Optional[int] = None,
        current_occupancy: Optional[int] = None,
        notes: Optional[str] = None,
        actor_role: str = "authority",
        actor_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if actor_role not in {"field_officer", "authority"}:
            raise PermissionError("Unauthorized to update operational availability.")
        prev = self.get_resource(resource_id, role=actor_role)
        if not prev:
            return None

        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE emergency_resources
                SET operational_status = ?, availability_status = ?,
                    capacity = ?, current_occupancy = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    operational_status or prev["operational_status"],
                    availability_status or prev["availability_status"],
                    capacity if capacity is not None else prev["capacity"],
                    current_occupancy if current_occupancy is not None else prev["current_occupancy"],
                    now_iso,
                    resource_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        updated = self.get_resource(resource_id, role=actor_role)
        _record_history(resource_id, "AVAILABILITY_UPDATED", actor_role, actor_id, prev, updated, notes)
        return updated

    def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0,
        resource_type: Optional[str] = None,
        operational_only: bool = True,
        role: str = "citizen",
        limit: int = 50,
    ) -> Dict[str, Any]:
        validate_coordinates(latitude, longitude)
        ensure_phase7_resource_schema()

        # Bounding-box pre-filter (~1 deg lat = 111 km)
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / max(15.0, 111.0 * abs(math.cos(math.radians(latitude))))
        clauses = [
            "latitude BETWEEN ? AND ?",
            "longitude BETWEEN ? AND ?",
            "verification_status = 'VERIFIED'",
        ]
        params: List[Any] = [
            latitude - lat_delta,
            latitude + lat_delta,
            longitude - lon_delta,
            longitude + lon_delta,
        ]
        if resource_type:
            clauses.append("resource_type = ?")
            params.append(resource_type.upper())
        if operational_only:
            clauses.append("operational_status != 'CLOSED'")

        conn = get_db_connection()
        try:
            rows = conn.execute(
                f"SELECT * FROM emergency_resources WHERE {' AND '.join(clauses)}",
                tuple(params),
            ).fetchall()
        finally:
            conn.close()

        matched: List[Dict[str, Any]] = []
        for r in rows:
            dist = haversine_km(latitude, longitude, r["latitude"], r["longitude"])
            if dist <= radius_km:
                matched.append(_row_to_resource(r, role=role, distance_km=dist))

        matched.sort(key=lambda x: x["distance_km"])
        return {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km,
            "distance_type": "straight_line_haversine_km",
            "distance_disclaimer": "Straight-line geographic distance only; does not represent road travel distance or travel time.",
            "count": len(matched[:limit]),
            "resources": matched[:limit],
        }

    def recommend_resources(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0,
        role: str = "citizen",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Transparent advisory ranking of verified nearby resources (never assumes unknown capacity is available)."""
        nearby = self.search_nearby(
            latitude=latitude, longitude=longitude, radius_km=radius_km,
            operational_only=True, role=role, limit=100,
        )
        op_rank = {"OPERATIONAL": 3, "TEMPORARILY_UNAVAILABLE": 1, "UNKNOWN": 2, "CLOSED": 0}
        avail_rank = {"AVAILABLE": 4, "LIMITED": 3, "UNKNOWN": 2, "FULL": 1, "UNAVAILABLE": 0}

        scored: List[Dict[str, Any]] = []
        for res in nearby["resources"]:
            o_s = op_rank.get(res["operational_status"], 1)
            a_s = avail_rank.get(res["availability_status"], 1)
            dist_pen = res["distance_km"] or 0.0
            priority_score = round(o_s * 30.0 + a_s * 20.0 - dist_pen, 2)
            scored.append(
                {
                    "resource": res,
                    "advisory_priority_score": priority_score,
                    "rationale": (
                        f"{res['resource_type']} ({res['operational_status']}, {res['availability_status']}) "
                        f"at {res['distance_km']} km straight-line distance."
                    ),
                }
            )
        scored.sort(key=lambda x: x["advisory_priority_score"], reverse=True)
        return {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km,
            "count": len(scored[:limit]),
            "advisory_disclaimer": (
                "Advisory ranking only based on straight-line distance, operational status, and availability. "
                "Does not represent road routing, spare hospital beds, or official deployment orders."
            ),
            "recommendations": scored[:limit],
        }

    def get_statistics(self, role: str = "authority") -> Dict[str, Any]:
        if role not in {"field_officer", "authority"}:
            raise PermissionError("Resource administration statistics are restricted to Field Officers and Authorities.")
        ensure_phase7_resource_schema()
        conn = get_db_connection()
        try:
            rows = conn.execute("SELECT * FROM emergency_resources").fetchall()
        finally:
            conn.close()

        by_cat: Dict[str, int] = {}
        ver = pend = rej = op = temp_un = full_sh = 0
        for r in rows:
            cat = r["resource_type"]
            by_cat[cat] = by_cat.get(cat, 0) + 1
            vs = r["verification_status"] or "PENDING"
            os_st = r["operational_status"] or "UNKNOWN"
            av_st = r["availability_status"] or "UNKNOWN"
            if vs == "VERIFIED":
                ver += 1
            elif vs == "REJECTED":
                rej += 1
            else:
                pend += 1
            if os_st == "OPERATIONAL":
                op += 1
            elif os_st == "TEMPORARILY_UNAVAILABLE":
                temp_un += 1
            if cat == "SHELTER" and av_st == "FULL":
                full_sh += 1

        return {
            "total_resources": len(rows),
            "verified_resources": ver,
            "pending_verification": pend,
            "rejected_resources": rej,
            "operational_resources": op,
            "temporarily_unavailable": temp_un,
            "full_shelters": full_sh,
            "by_category": by_cat,
        }

    def get_history(self, resource_id: str, role: str = "authority") -> List[Dict[str, Any]]:
        if role not in {"field_officer", "authority"}:
            raise PermissionError("Verification history is restricted to Field Officers and Authorities.")
        ensure_phase7_resource_schema()
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM resource_history WHERE resource_id = ? ORDER BY timestamp DESC",
                (resource_id,),
            ).fetchall()
            return [
                {
                    "history_id": r["history_id"],
                    "resource_id": r["resource_id"],
                    "action": r["action"],
                    "actor_role": r["actor_role"],
                    "actor_id": r["actor_id"],
                    "notes": r["notes"],
                    "timestamp": r["timestamp"],
                }
                for r in rows
            ]
        finally:
            conn.close()

    async def import_osm_candidates(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        actor_role: str = "authority",
    ) -> Dict[str, Any]:
        """
        Query OpenStreetMap Overpass API for candidate hospitals/shelters.
        Imported facilities are ALWAYS marked PENDING verification and UNKNOWN status.
        """
        if actor_role not in {"field_officer", "authority"}:
            raise PermissionError("OSM candidate import is restricted to Field Officers and Authorities.")
        validate_coordinates(latitude, longitude)
        radius_m = int(min(radius_km, 25.0) * 1000)
        query = (
            f"[out:json][timeout:15];"
            f"(node[\"amenity\"=\"hospital\"](around:{radius_m},{latitude},{longitude});"
            f"node[\"amenity\"=\"shelter\"](around:{radius_m},{latitude},{longitude}););"
            f"out center 20;"
        )
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            elements = resp.json().get("elements", [])

        imported: List[Dict[str, Any]] = []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name:
                continue
            amenity = tags.get("amenity", "")
            rtype = "HOSPITAL" if amenity == "hospital" else "SHELTER"
            rec = self.create_resource(
                {
                    "resource_name": name,
                    "resource_type": rtype,
                    "description": f"Imported OSM candidate ({amenity}); requires official verification.",
                    "latitude": float(el["lat"]),
                    "longitude": float(el["lon"]),
                    "source": "OpenStreetMap Overpass API (ODbL)",
                },
                actor_role=actor_role,
                actor_id="osm_importer",
            )
            imported.append(rec)

        return {
            "imported_count": len(imported),
            "verification_status": "PENDING",
            "note": "All OSM candidates are marked PENDING verification and UNKNOWN availability.",
            "resources": imported,
        }


resource_service = ResourceService()
