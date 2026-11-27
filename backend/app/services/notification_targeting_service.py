from typing import Dict, Any, List

from app.db.database import get_db_connection, ensure_phase9_schema
from app.services.resource_service import haversine_km


class NotificationTargetingService:
    """
    Selects eligible recipients for an alert based on role, jurisdiction,
    explicitly selected location/state/district, and notification preferences.
    Never exposes recipient emails or device tokens to other users.
    """

    def find_eligible_recipients(self, alert: Dict[str, Any]) -> List[Dict[str, Any]]:
        ensure_phase9_schema()
        alert_state = (alert.get("state") or "").strip().lower()
        alert_lat = alert.get("latitude")
        alert_lon = alert.get("longitude")
        is_public = bool(alert.get("is_official_public_warning", True))

        conn = get_db_connection()
        try:
            users = conn.execute(
                """
                SELECT u.user_id, u.email, u.full_name, u.role, u.assigned_state, u.assigned_district,
                       p.email_enabled, p.push_enabled, p.preferred_state, p.preferred_district,
                       p.latitude AS pref_lat, p.longitude AS pref_lon
                FROM users u
                LEFT JOIN notification_preferences p ON u.user_id = p.user_id
                WHERE u.is_active = 1
                """
            ).fetchall()

            devices = conn.execute(
                "SELECT device_id, user_id, fcm_token, platform FROM notification_devices WHERE is_active = 1"
            ).fetchall()
        finally:
            conn.close()

        dev_by_user: Dict[str, List[Dict[str, Any]]] = {}
        for d in devices:
            dev_by_user.setdefault(d["user_id"], []).append(dict(d))

        eligible: List[Dict[str, Any]] = []
        for u in users:
            role = u["role"].upper()
            if not is_public and role == "CITIZEN":
                continue

            # Geographic / jurisdiction match
            user_state = (u["assigned_state"] or u["preferred_state"] or "").strip().lower()
            state_match = (not alert_state) or (not user_state) or (alert_state == user_state)

            # Coordinate proximity check if citizen/officer shared explicit preferred coords (50 km radius)
            coord_match = True
            if alert_lat is not None and alert_lon is not None and u["pref_lat"] is not None and u["pref_lon"] is not None:
                coord_match = haversine_km(alert_lat, alert_lon, u["pref_lat"], u["pref_lon"]) <= 50.0

            if not (state_match and coord_match):
                continue

            eligible.append(
                {
                    "user_id": u["user_id"],
                    "email": u["email"],
                    "role": role,
                    "email_enabled": bool(1 if u["email_enabled"] is None else u["email_enabled"]),
                    "push_enabled": bool(1 if u["push_enabled"] is None else u["push_enabled"]),
                    "devices": dev_by_user.get(u["user_id"], []),
                }
            )
        return eligible


notification_targeting_service = NotificationTargetingService()
